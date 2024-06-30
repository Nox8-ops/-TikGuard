import time
import random
import logging
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tqdm import tqdm
from termcolor import colored
from rich.console import Console
from rich.logging import RichHandler
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

console = Console()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[RichHandler()])

VERSION = "1.0.0-beta"
DEVELOPER = "@Nox9"

class TikGuard:
    def __init__(self, proxies=None, max_retries=3, retry_delay=5):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        self.max_retries = max_retries
        self.retry_delay = retry_delay  # seconds
        self.proxies = proxies if proxies else []

    def switch_proxy(self):
        if self.proxies:
            proxy = random.choice(self.proxies)
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument(f'--proxy-server={proxy}')
            self.driver.quit()
            self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
            logging.info(f"Switched to proxy: {proxy}")

    def get_report_url(self, video_url):
        for attempt in range(self.max_retries):
            try:
                self.switch_proxy()
                self.driver.get(video_url)
                time.sleep(5)  # زيادة وقت الانتظار للتأكد من تحميل الصفحة بالكامل

                try:
                    report_button = self.driver.find_element(By.XPATH, '//*[contains(@class, "report-button-class")]')
                    if report_button:
                        return report_button.get_attribute('data-report-url')
                except:
                    pass
                
                scripts = self.driver.find_elements(By.TAG_NAME, 'script')
                for script in scripts:
                    if 'reportUrl' in script.get_attribute('innerHTML'):
                        report_url_match = re.search(r'reportUrl":"(https[^"]+)"', script.get_attribute('innerHTML'))
                        if report_url_match:
                            return report_url_match.group(1)

            except Exception as e:
                logging.error(f"Error fetching video page: {e}, retrying in {self.retry_delay} seconds...", exc_info=True)
                time.sleep(self.retry_delay)
        return None

    def submit_report(self, report_url, reason):
        payload = {
            'reason': reason,
            'additional_info': 'Spam or inappropriate content'
        }
        for attempt in range(self.max_retries):
            try:
                self.switch_proxy()
                self.driver.get(report_url)
                time.sleep(2)  # Wait for the report page to load
                self.driver.find_element(By.NAME, 'reason').send_keys(reason)
                self.driver.find_element(By.NAME, 'additional_info').send_keys('Spam or inappropriate content')
                self.driver.find_element(By.TAG_NAME, 'form').submit()
                return "Report submitted successfully!"
            except Exception as e:
                logging.error(f"Error submitting report: {e}, retrying in {self.retry_delay} seconds...", exc_info=True)
                time.sleep(self.retry_delay)
        return "Failed to submit report."

def print_logo():
    logo = """
████████╗██╗██╗  ██╗ ██████╗ ██╗   ██╗ ██████╗  █████╗ ██████╗ 
╚══██╔══╝██║██║  ██║██╔═══██╗██║   ██║██╔════╝ ██╔══██╗██╔══██╗
   ██║   ██║███████║██║   ██║██║   ██║██║  ███╗███████║██████╔╝
   ██║   ██║██╔══██║██║   ██║██║   ██║██║   ██║██╔══██║██╔═══╝ 
   ██║   ██║██║  ██║╚██████╔╝╚██████╔╝╚██████╔╝██║  ██║██║     
   ╚═╝   ╚═╝╚═╝  ╚═╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝     
    """
    console.print(colored(logo, 'cyan'))
    console.print(colored(f"Version: {VERSION} - Developed by: {DEVELOPER}", 'green'))

class TikGuardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TikGuard - TikTok Reporting Tool")

        mainframe = ttk.Frame(root, padding="10")
        mainframe.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.video_url_label = ttk.Label(mainframe, text="Video URL:")
        self.video_url_label.grid(row=1, column=1, sticky=tk.W)
        self.video_url_entry = ttk.Entry(mainframe, width=50)
        self.video_url_entry.grid(row=1, column=2, columnspan=2)

        self.reason_label = ttk.Label(mainframe, text="Reason:")
        self.reason_label.grid(row=2, column=1, sticky=tk.W)
        self.reason_entry = ttk.Entry(mainframe, width=50)
        self.reason_entry.grid(row=2, column=2, columnspan=2)

        self.proxies_file_label = ttk.Label(mainframe, text="Proxies File (optional):")
        self.proxies_file_label.grid(row=3, column=1, sticky=tk.W)
        self.proxies_file_entry = ttk.Entry(mainframe, width=40)
        self.proxies_file_entry.grid(row=3, column=2)
        self.proxies_file_button = ttk.Button(mainframe, text="Browse", command=self.browse_proxies_file)
        self.proxies_file_button.grid(row=3, column=3)

        self.submit_button = ttk.Button(mainframe, text="Submit Report", command=self.submit_report)
        self.submit_button.grid(row=4, column=2, pady=10)

        self.status_label = ttk.Label(mainframe, text="", foreground="red")
        self.status_label.grid(row=5, column=1, columnspan=3)

        for child in mainframe.winfo_children(): 
            child.grid_configure(padx=5, pady=5)

    def browse_proxies_file(self):
        filename = filedialog.askopenfilename()
        self.proxies_file_entry.delete(0, tk.END)
        self.proxies_file_entry.insert(0, filename)

    def submit_report(self):
        video_url = self.video_url_entry.get()
        reason = self.reason_entry.get()
        proxies_file = self.proxies_file_entry.get()

        if not video_url or not reason:
            messagebox.showerror("Error", "Please enter both video URL and reason.")
            return

        proxies = []
        if proxies_file:
            try:
                with open(proxies_file, 'r') as file:
                    proxies.extend([line.strip() for line in file])
            except Exception as e:
                messagebox.showerror("Error", f"Failed to read proxies file: {e}")
                return

        self.status_label.config(text="Submitting report...", foreground="blue")
        self.root.update()

        reporter = TikGuard(proxies=proxies)
        report_url = reporter.get_report_url(video_url)
        if report_url:
            with tqdm(total=100, desc="Submitting report", ncols=100) as pbar:
                result = reporter.submit_report(report_url, reason)
                for i in range(100):
                    time.sleep(0.01)
                    pbar.update(1)
                self.status_label.config(text=result, foreground="green" if "successfully" in result else "red")
        else:
            self.status_label.config(text="Failed to find report URL.", foreground="red")

def main():
    print_logo()

    root = tk.Tk()
    app = TikGuardApp(root)
    root.mainloop()

if __name__ == '__main__':
    main()
