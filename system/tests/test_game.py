import os
import time
import unittest
from pathlib import Path

from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
import selenium.webdriver.support.ui as ui
import selenium.webdriver.support.expected_conditions as EC

from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager


class GameTests(unittest.TestCase):
    debug = False

    def setUp(self):
        options = webdriver.ChromeOptions()
        if not self.debug:
            options.add_argument('--headless')

        driver = webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install()),
            options=options)
        driver.delete_all_cookies()
        self.wait = ui.WebDriverWait(driver, 30)  # timeout after 30 seconds
        self.driver = driver
        driver.get("https://www.newrecruit.eu/app")
        print("Loading NR")

        driver.execute_script('localStorage.setItem("local", "true")')
        # seems to end up running before the system initializes, so we don't need to refresh

        print("Waiting up to 30 seconds for the theme pop-up")
        try:
            theme_button_elements = self.wait.until(lambda drv:
                                                    drv.find_elements(By.XPATH, "//*[text()='Close']"))
            if len(theme_button_elements) > 0:
                print("Skipping the theme pop-up")
                theme_button_elements[0].click()
        except TimeoutException:
            print("No theme pop-up to skip")

    def load_system(self, system_name):
        default_data_directory = os.getenv("DEFAULT_DATA_DIRECTORY", os.path.expanduser("~/BattleScribe/data/"))
        self.game_directory = str(os.path.join(default_data_directory, system_name))
        # add game system by clicking import
        print("Looking for system import")
        import_system_buttons = self.wait.until(lambda drv:
                                                drv.find_elements(By.XPATH, "//input[@type='file']"))
        if len(import_system_buttons) > 0:
            print("Found the system import button")
            import_system_buttons[0].send_keys(self.game_directory)

        # Load the 1st system.
        import_buttons = self.wait.until(lambda drv:
                                         drv.find_elements(By.CSS_SELECTOR,
                                                           "#mainContent > fieldset > div > div > div:nth-child(1)"))
        if len(import_buttons) > 0:
            print("Loading the first game system")
            import_buttons[0].click()

    def load_list(self, roster_filename: str):
        # add list by clicking import
        test_list = os.path.join(self.game_directory, 'tests', roster_filename)
        import_list_element = self.wait.until(lambda drv:
                                              drv.find_elements(By.ID, "importBs")
                                              )

        if len(import_list_element) > 0:
            print("Uploading list to the import list button")
            import_list_element[0].send_keys(test_list)

        # Load the first list
        self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "listName"))).click()
        print("Loading the first list")

        # Wait until the list has loaded
        print("Waiting for the list to load...")
        self.wait.until(lambda drv:
                        drv.find_element(By.CLASS_NAME, 'titreRoster'))

    def tearDown(self):
        if self.debug:
            # 60 seconds for me to mess around in
            time.sleep(60)
        self.driver.quit()

    def get_error_list(self):
        errors = self.driver.execute_script("return $debugOption.allErrors.map(error => ({"
                                            "msg: error.msg,"
                                            "constraint_id:error.constraint.id,"
                                            "}))")
        if self.debug:
            print("$debugOption for list")
            print(errors)
        return errors

    def get_squad_cost(self, primary_category, unit_name, force_index=0):
        script_to_run = (f" $debugOption.state.getChilds()[{force_index}].getChilds()[0].getChilds()"
                         f".filter(entry => entry.name == '{primary_category}')[0].getChilds()"
                         f".filter(entry => entry.name == '{unit_name}')[0].totalCosts")
        if self.debug:
            print(script_to_run)
        costs = self.driver.execute_script(f"return {script_to_run}")
        if len(costs) == 1:
            return list(costs.values())[0]
        return costs

    def test_LA_5_errors(self):
        self.load_system('horus-heresy')
        self.load_list('Empty Validation Test.ros')
        errors = self.get_error_list()
        self.assertEqual(5, len(errors), "There are 5 errors in an empty space marine list")

    def test_dt_does_not_affect_squad_cost(self):
        self.load_system('horus-heresy')
        self.load_list('Dedicated Transport Squad Costs.ros')
        squad_cost = self.get_squad_cost("Troops:", "Tactical Support Squad")
        print(squad_cost)
        self.assertEqual(170, squad_cost, "TSS does not count the rhino as a model")


if __name__ == '__main__':
    unittest.main()
