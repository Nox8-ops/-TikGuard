import requests
from bs4 import BeautifulSoup
import re
import time
import random
import logging
import tkinter as tk
from tkinter import messagebox, filedialog
from tqdm import tqdm
from termcolor import colored
from rich.console import Console
from rich.logging import RichHandler

console = Console()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[RichHandler()])

VERSION = "1.0.0-beta"
DEVELOPER = "@Nox9"

class TikGuard:
    def __init__(self, proxies=None, max_retries=3, retry_delay=5):
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Content-Type': 'application/json'
        }
        self.max_retries = max_retries
        self.retry_delay = retry_delay  # seconds
        self.proxies = proxies if proxies else []

    def switch_proxy(self):
        if self.proxies:
            proxy = random.choice(self.proxies)
            self.session.proxies = {
                'http': proxy,
                'https': proxy
            }
            logging.info(f"Switched to proxy: {proxy}")

    def get_report_url(self, video_url):
        for attempt in range(self.max_retries):
            try:
                self.switch_proxy()
                response = self.session.get(video_url, headers=self.headers)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')

                # Attempt to find the report URL in different ways
                report_button = soup.find('button', {'class': 'report-button-class'})
                if report_button and report_button.has_attr('data-report-url'):
                    return report_button['data-report-url']
                
                scripts = soup.find_all('script')
                for script in scripts:
                    if 'reportUrl' in script.text:
                        report_url_match = re.search(r'reportUrl":"(https[^"]+)"', script.text)
                        if report_url_match:
                            return report_url_match.group(1)
                
                # Additional pattern matching if needed
                pattern = re.compile(r'\"reportUrl\":\"(https[^\"]+)\"')
                matches = pattern.findall(response.text)
                if matches:
                    return matches[0]

            except requests.exceptions.RequestException as e:
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
                response = self.session.post(report_url, json=payload, headers=self.headers)
                response.raise_for_status()
                return "Report submitted successfully!"
            except requests.exceptions.RequestException as e:
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

        self.video_url_label = tk.Label(root, text="Video URL:")
        self.video_url_label.pack()
        self.video_url_entry = tk.Entry(root, width=50)
        self.video_url_entry.pack()

        self.reason_label = tk.Label(root, text="Reason:")
        self.reason_label.pack()
        self.reason_entry = tk.Entry(root, width=50)
        self.reason_entry.pack()

        self.proxies_file_label = tk.Label(root, text="Proxies File (optional):")
        self.proxies_file_label.pack()
        self.proxies_file_entry = tk.Entry(root, width=50)
        self.proxies_file_entry.pack()
        self.proxies_file_button = tk.Button(root, text="Browse", command=self.browse_proxies_file)
        self.proxies_file_button.pack()

        self.submit_button = tk.Button(root, text="Submit Report", command=self.submit_report)
        self.submit_button.pack()

        self.status_label = tk.Label(root, text="", fg="red")
        self.status_label.pack()

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

        self.status_label.config(text="Submitting report...", fg="blue")
        self.root.update()

        reporter = TikGuard(proxies=proxies)
        report_url = reporter.get_report_url(video_url)
        if report_url:
            with tqdm(total=100, desc="Submitting report", ncols=100) as pbar:
                result = reporter.submit_report(report_url, reason)
                for i in range(100):
                    time.sleep(0.01)
                    pbar.update(1)
                self.status_label.config(text=result, fg="green" if "successfully" in result else "red")
        else:
            self.status_label.config(text="Failed to find report URL.", fg="red")

def main():
    print_logo()

    root = tk.Tk()
    app = TikGuardApp(root)
    root.mainloop()

if __name__ == '__main__':
    main()
