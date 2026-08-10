from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.on("console", lambda msg: print(f"Browser console: {msg.text}"))
        page.on("pageerror", lambda err: print(f"Browser error: {err}"))
        
        print("Navigating to local server...")
        try:
            page.goto("http://localhost:8000/lms/activity/", wait_until="networkidle")
            print("Clicking medicacion...")
            page.evaluate("document.querySelectorAll('.incident-type-btn')[1].click()")
            page.wait_for_timeout(1000)
            
            # check classes
            btn_class = page.evaluate("document.querySelectorAll('.incident-type-btn')[1].className")
            print("Btn 2 class:", btn_class)
            
            # check tab text
            tab_text = page.evaluate("document.getElementById('step-tab-2').innerText")
            print("Tab 2 text:", tab_text)
            
        except Exception as e:
            print("Error:", e)
            
        browser.close()

if __name__ == "__main__":
    run()
