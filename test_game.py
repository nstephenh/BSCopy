import os
import time
import unittest
from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
import selenium.webdriver.support.ui as ui

from settings import default_data_directory


class MyTestCase(unittest.TestCase):

    def test_game(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        driver = webdriver.Chrome(
            service=webdriver.chrome.service.Service(executable_path='system/tests/chromedriver/chromedriver.exe'),
            options=options)
        driver.delete_all_cookies()
        wait = ui.WebDriverWait(driver, 30)  # timeout after 30 seconds

        driver.get("https://www.newrecruit.eu/app/MySystems")
        print("Loading NR")

        driver.execute_script('localStorage.setItem("local", "true")')
        # seems to end up running before the system initializes, so we don't need to refresh

        print("Waiting up to 30 seconds for the theme pop-up")
        try:
            theme_button_elements = wait.until(lambda drv:
                                               drv.find_elements(By.XPATH, "//*[text()='Keep current Theme']"))
            if len(theme_button_elements) > 0:
                print("Skipping the theme pop-up")
                theme_button_elements[0].click()
        except TimeoutException:
            print("No theme pop-up to skip")

        game_directory = os.path.join(default_data_directory, 'horus-heresy')
        # add game system by clicking import
        print("Looking for system import")
        import_system_buttons = wait.until(lambda drv:
                                           drv.find_elements(By.XPATH, "//input[@type='file']"))
        if len(import_system_buttons) > 0:
            print("Found the system import button")
            import_system_buttons[0].send_keys(game_directory)

        # Load the 1st system.
        import_buttons = wait.until(lambda drv:
                                    drv.find_elements(By.CSS_SELECTOR,
                                                      "#mainContent > fieldset > div > div > div:nth-child(1)"))
        if len(import_buttons) > 0:
            print("Loading the first game system")
            import_buttons[0].click()

        # add list by clicking import
        test_list = os.path.join(game_directory, 'tests', 'Empty Validation Test.ros')
        import_list_element = wait.until(lambda drv:
                                         drv.find_elements(By.ID, "importBs")
                                         )

        if len(import_list_element) > 0:
            print("Uploading list to the import list button")
            import_list_element[0].send_keys(test_list)

        # Load the first list
        lists = wait.until(lambda drv:
                           drv.find_elements(By.CLASS_NAME, "listName"))
        if len(lists) > 0:
            print("Loading the first list")
            lists[0].click()

        # Wait until the list has loaded
        print("Waiting for the list to load...")
        wait.until(lambda drv:
                   drv.find_element(By.CLASS_NAME, 'titreRoster'))

        # Check for error list
        print("$debugOption for list")
        errors = driver.execute_script("return $debugOption.allErrors.map(error => ({"
                                       "msg: error.msg,"
                                       "constraint_id:error.constraint.id,"
                                       "}))")
        print(errors)
        # 60 seconds for me to mess around in
        # time.sleep(60)
        driver.quit()
        self.assertEqual(5, len(errors), "There are 5 errors in an empty space marine list")


if __name__ == '__main__':
    unittest.main()
