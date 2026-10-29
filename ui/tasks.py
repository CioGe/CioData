# -*- coding: utf-8 -*-
"""
后台任务运行器：所有耗时操作（LLM调用/文件加载/Databricks连接）都放线程里执行，
结果通过队列回到主线程回调，UI 全程不卡。
单任务槽位：同一时间只跑一个后台任务，避免并发把界面搞乱。

使用约定：
    def work():
        df, err = load_csv(path)
        if err:
            raise TaskFailed(err)      # 可预期错误 → 弹给用户看
        return df
    tasks.run("加载数据", work, on_success=..., on_error=...)
"""

import queue
import threading
import traceback

import i18n


class TaskFailed(Exception):
    """业务层主动抛出的可预期错误，消息直接展示给用户。"""


class TaskRunner:
    def __init__(self, root, poll_ms: int = 60):
        self._root = root
        self._queue: "queue.Queue" = queue.Queue()
        self._busy = False
        self._poll_ms = poll_ms
        self._task_name = ""
        self._schedule_poll()

    def _schedule_poll(self):
        try:
            self._root.after(self._poll_ms, self._poll)
        except Exception:
            pass  # 窗口已销毁

    @property
    def busy(self) -> bool:
        return self._busy

    @property
    def task_name(self) -> str:
        return self._task_name

    def run(self, name, fn, on_success=None, on_error=None, on_start=None, on_finish=None) -> bool:
        """
        提交后台任务。fn 在子线程执行，返回值传给 on_success(result)。
        fn 抛 TaskFailed/Exception → on_error(msg)。所有回调均在主线程执行。
        on_start 在线程启动前于主线程同步调用（可切换加载态）。
        """
        if self._busy:
            if on_error:
                on_error(i18n.t("task.busy", name=self._task_name))
            return False
        self._busy = True
        self._task_name = name
        if on_start:
            try:
                on_start()
            except Exception:
                traceback.print_exc()

        callbacks = (on_success, on_error, on_finish)

        def _worker():
            err_msg = None
            result = None
            try:
                result = fn()
            except TaskFailed as e:
                err_msg = str(e)
            except Exception as e:
                err_msg = f"{type(e).__name__}: {e}"
                traceback.print_exc()
            self._queue.put((callbacks, result, err_msg))

        threading.Thread(target=_worker, daemon=True, name=f"task-{name}").start()
        return True

    def _poll(self):
        try:
            while True:
                callbacks, result, err_msg = self._queue.get_nowait()
                self._busy = False
                on_success, on_error, on_finish = callbacks
                try:
                    if err_msg is not None:
                        if on_error:
                            on_error(err_msg)
                    else:
                        if on_success:
                            on_success(result)
                except Exception:
                    traceback.print_exc()
                finally:
                    if on_finish:
                        try:
                            on_finish()
                        except Exception:
                            traceback.print_exc()
        except queue.Empty:
            pass
        finally:
            self._schedule_poll()
