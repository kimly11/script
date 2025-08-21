import pyautogui
import pytesseract
import cv2
import time

# Step 1: Check Panel for new request (assume region where new requests appear)
panel_region = (x, y, width, height)  # fill with your panel screen coordinates

def get_panel_text():
    img = pyautogui.screenshot(region=panel_region)
    img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    text = pytesseract.image_to_string(img_cv)
    return text

def paste_to_analyzer(text):
    # activate analyzer window (you may use pygetwindow or hotkeys)
    pyautogui.hotkey('alt', 'tab')  # example: switch window, customize as needed
    time.sleep(1)
    pyautogui.click(analyzer_input_x, analyzer_input_y)  # click input box
    pyautogui.typewrite(text)
    pyautogui.press('enter')

def check_bank():
    # take screenshot of bank result area in analyzer
    bank_region = (x2, y2, w2, h2)
    img = pyautogui.screenshot(region=bank_region)
    img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    bank_text = pytesseract.image_to_string(img_cv).strip().upper()
    return bank_text

def vysor_check(bank_name):
    # activate vysor window, then do steps depending on bank
    pyautogui.hotkey('alt', 'tab')
    time.sleep(1)
    if bank_name == "BCA":
        # click/check BCA in Vysor
        pyautogui.click(bca_button_x, bca_button_y)
    elif bank_name == "DANA":
        pyautogui.click(dana_button_x, dana_button_y)

while True:
    panel_text = get_panel_text()
    if "NEW REQUEST" in panel_text.upper():
        paste_to_analyzer(panel_text)
        time.sleep(3)  # wait for analyzer to process
        bank = check_bank()
        vysor_check(bank)
    time.sleep(5)  # wait before checking again
