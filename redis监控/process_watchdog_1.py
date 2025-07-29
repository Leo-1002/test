#!/usr/bin/env python3
import os
import time
import subprocess
import signal
from datetime import datetime
import psutil

# 配置部分
PROCESS_NAME = "time.py"  # 需要守护的脚本名
PROCESS_CMD = ["python3", PROCESS_NAME]  # 完整启动命令
MAX_RESTARTS = 5  # 最大重启次数
CHECK_INTERVAL = 30  # 检查间隔(秒)
LOG_FILE = "watchdog.log"  # 守护日志路径
OUTPUT_LOG = "strategy.log"  # 被守护进程的输出日志
GRACE_PERIOD = 10  # 进程启动后的宽限期(秒)


class ProcessGuardian:
    def __init__(self):
        self.restart_count = 0
        self.process = None
        self.pid_file = f"{PROCESS_NAME}.pid"
        self.last_pid = None
        self.last_start_time = None

    def log(self, message):
        """带时间戳的日志记录"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] {message}"
        print(log_msg)
        with open(LOG_FILE, "a") as f:
            f.write(log_msg + "\n")

    def get_process_info(self):
        """获取目标进程信息"""
        try:
            for proc in psutil.process_iter(['pid', 'cmdline']):
                try:
                    if (proc.info['cmdline'] and
                            len(proc.info['cmdline']) >= 2 and
                            proc.info['cmdline'][0] == 'python3' and
                            proc.info['cmdline'][1].endswith(PROCESS_NAME) and
                            proc.pid != os.getpid()):
                        return proc.pid
                except (psutil.NoSuchProcess, psutil.AccessDenied, IndexError):
                    continue
            return None
        except Exception as e:
            self.log(f"获取进程信息出错: {str(e)}")
            return None

    def is_process_healthy(self, pid):
        """检查进程是否健康运行"""
        try:
            proc = psutil.Process(pid)

            # 检查进程状态
            status = proc.status()
            if status in ('zombie', 'dead'):
                self.log(f"进程 {pid} 状态异常 ({status})")
                return False

            # 检查进程运行时间（避免刚启动的进程被误判）
            if self.last_start_time and (time.time() - self.last_start_time) < GRACE_PERIOD:
                return True

            # 检查CPU使用率（可选）
            try:
                cpu_percent = proc.cpu_percent(interval=0.1)
                if cpu_percent > 90:  # 如果CPU占用过高
                    self.log(f"进程 {pid} CPU占用过高: {cpu_percent}%")
                    return False
            except:
                pass

            return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False
        except Exception as e:
            self.log(f"检查进程健康状态出错: {str(e)}")
            return False

    def start_process(self):
        """启动目标进程并记录PID"""
        try:
            # 检查是否已有相同进程在运行
            existing_pid = self.get_process_info()
            if existing_pid:
                self.log(f"进程已存在 (PID:{existing_pid})，跳过启动")
                return True

            # 检查目标脚本是否存在
            if not os.path.exists(PROCESS_NAME):
                self.log(f"错误：目标脚本 {PROCESS_NAME} 不存在")
                return False

            # 启动新进程
            with open(OUTPUT_LOG, "a") as log_file:
                self.process = subprocess.Popen(
                    PROCESS_CMD,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    start_new_session=True  # 创建新会话，但不使用preexec_fn
                )

            self.last_pid = self.process.pid
            self.last_start_time = time.time()

            # 写入PID文件
            with open(self.pid_file, "w") as f:
                f.write(str(self.last_pid))

            self.log(f"成功启动进程 {PROCESS_NAME} (PID:{self.last_pid})")
            return True
        except FileNotFoundError:
            self.log(f"错误：找不到命令 {' '.join(PROCESS_CMD)}")
            return False
        except Exception as e:
            self.log(f"启动进程失败: {str(e)}")
            return False

    def cleanup(self):
        """清理残留PID文件"""
        if os.path.exists(self.pid_file):
            try:
                os.remove(self.pid_file)
            except Exception as e:
                self.log(f"清理PID文件失败: {str(e)}")

    def stop_process(self, pid):
        """优雅停止进程"""
        try:
            proc = psutil.Process(pid)
            proc.terminate()  # 先发送SIGTERM
            try:
                proc.wait(timeout=10)  # 等待10秒
            except psutil.TimeoutExpired:
                proc.kill()  # 强制终止
                self.log(f"强制终止进程 {pid}")
            return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return True
        except Exception as e:
            self.log(f"停止进程 {pid} 出错: {str(e)}")
            return False

    def run(self):
        """主监控循环"""
        self.log(f"守护进程启动，监控目标: {' '.join(PROCESS_CMD)}")
        self.cleanup()

        try:
            while self.restart_count < MAX_RESTARTS:
                current_pid = self.get_process_info()

                if current_pid:
                    if self.is_process_healthy(current_pid):
                        self.restart_count = 0  # 重置计数器
                        self.log(f"进程运行正常 (PID:{current_pid})")
                    else:
                        self.log(f"进程 {current_pid} 不健康，准备重启")
                        self.stop_process(current_pid)
                        time.sleep(1)  # 等待进程完全退出
                else:
                    self.log("未检测到目标进程")

                # 如果需要重启
                if not current_pid or not self.is_process_healthy(current_pid):
                    if self.restart_count > 0:
                        self.log(f"尝试重启 ({self.restart_count}/{MAX_RESTARTS})")

                    if self.start_process():
                        self.restart_count += 1
                        time.sleep(GRACE_PERIOD)  # 等待进程初始化
                    else:
                        time.sleep(60)  # 启动失败时延长等待

                time.sleep(CHECK_INTERVAL)

            self.log(f"达到最大重启次数 {MAX_RESTARTS}，停止守护")
        except KeyboardInterrupt:
            self.log("收到中断信号，停止守护")
        except Exception as e:
            self.log(f"守护进程异常: {str(e)}")
        finally:
            self.cleanup()


if __name__ == "__main__":
    guardian = ProcessGuardian()
    guardian.run()
