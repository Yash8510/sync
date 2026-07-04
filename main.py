"""
main assistant entry point
"""

import torch  # pre-import torch to avoid getting DLL collision error with PyQt6

import asyncio
import logging
import sys
import threading

from PyQt6.QtCore import QObject
from PyQt6.QtWidgets import QApplication

from audio.orchestrator import AudioSpeechPipeline
from core.config import load_config
from core.event_bus import EventBus
from core.logging_setup import config_logging
from ui.main_window import MainWindow
from ui.bridge import PyQtEventBridge

logger = logging.getLogger("assistant.main")


class SafetyBridge(QObject):
    """Bridges synchronous safety propts in background threads to asynchronous PyQt dialogs on the main thread"""


async def run_pipeline(pipeline: AudioSpeechPipeline) -> None:
    """Async worker thread running mic/VAD pipeline listener"""
    try:
        await pipeline.start_listening()
        # Run loop infinitely to handle incoming request
        while True:
            if pipeline._is_running:
                text = await pipeline.get_user_utterance()  # get user text
                if text and text.strip():
                    await pipeline.process_utterance(text)  # process user command
            else:
                await asyncio.sleep(0.5)
    except asyncio.CancelledError:
        logger.info("Background voice pipeline task cancelled")
        if pipeline._is_running:
            await pipeline.stop_listening()
    except Exception as e:
        logger.exception("Error in background voice pipeline: %s", e)


def start_async_loop(loop: asyncio.AbstractEventLoop, pipeline: AudioSpeechPipeline):
    """Entry point for background worker thread"""
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run_pipeline(pipeline))
    except Exception as e:
        logger.error("Async worker thread encountered error: %s", e)
    finally:
        try:
            pending = asyncio.all_tasks(loop)
            if pending:
                for task in pending:
                    task.cancel()
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            loop.run_until_complete(loop.shutdown_asyncgens())
        except Exception as e:
            logger.error("Error during asyncio loop shutdown: %s", e)
        finally:
            loop.close()


def main():
    # app instance
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)  # minimize window when closed

    # load config file
    config = load_config("config/default.yaml")
    config_logging(config.log_level, str(config.raw.get("logging").get("file")))
    logger.info("=== Starting assistant application ===")

    # <----------loadup the important things first---------->
    # 1. Initialize EventBus
    # 2. Audio Pipeline Orchestrator instantiation
    # 3. Initialize PyQt Event Bridge
    # 4. Setup Main Window Instance

    # initializing eventbus
    event_bus = EventBus()

    # background async loop instanced
    bg_loop = asyncio.new_event_loop()

    # audio pipeline orchestrator
    speech_cfg = config.raw.get("speech")
    pipeline = AudioSpeechPipeline(
        event_bus=event_bus,
        speech_cfg=speech_cfg
    )

    # setup event bridge
    event_bridge = PyQtEventBridge(event_bus)

    # window setup and show
    window = MainWindow(
        event_bridge,
        audio_capture=pipeline.capture
    )
    window.show()  # display window
    # <----------END---------->


    # <----------Starting background worker thread and PyQt eventloop---------->
    # start background worker thread to run asyncio event loop
    bg_thread = threading.Thread(
        target=start_async_loop,
        args=(bg_loop, pipeline),
        daemon=True
    )
    bg_thread.start()
    logger.info("Background threaded voice loop started successfully")

    # Start PyQt eventloop
    exit_code = app.exec()
    # <----------END---------->


    # <----------Safely cleaning up and shutting down the assistant---------->
    # cleanup on exit
    logger.info("=== Shutting Down App ===")
    event_bridge._unsubscribe_all()  # unsubscribe all events

    # cancel all tasks in the background loop thread-safely
    def cancel_tasks():
        for task in asyncio.all_tasks(bg_loop):
            task.cancel()

    bg_loop.call_soon_threadsafe(cancel_tasks)
    bg_thread.join(timeout=3)
    logger.info("Main loop terminated, exiting")
    sys.exit(exit_code)
    # <----------END---------->


if __name__ == "__main__":
    main()
