#main2.py

import data
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# no modificar
def retrieve_phone_code(driver) -> str:
    """Este código devuelve un número de confirmación de teléfono y lo devuelve como un string.
    Utilízalo cuando la aplicación espere el código de confirmación para pasarlo a tus pruebas.
    El código de confirmación del teléfono solo se puede obtener después de haberlo solicitado en la aplicación."""

    import json
    import time
    from selenium.common import WebDriverException
    code = None
    for i in range(10):
        try:
            logs = [log["message"] for log in driver.get_log('performance') if log.get("message")
                    and 'api/v1/number?number' in log.get("message")]
            for log in reversed(logs):
                message_data = json.loads(log)["message"]
                body = driver.execute_cdp_cmd('Network.getResponseBody',
                                              {'requestId': message_data["params"]["requestId"]})
                code = ''.join([x for x in body['body'] if x.isdigit()])
        except WebDriverException:
            time.sleep(1)
            continue
        if not code:
            raise Exception("No se encontró el código de confirmación del teléfono.\n"
                            "Utiliza 'retrieve_phone_code' solo después de haber solicitado el código en tu aplicación.")
        return code


class UrbanRoutesPage:
    from_field = (By.ID, 'from')
    to_field = (By.ID, 'to')

    def __init__(self, driver):
        self.driver = driver

    def set_from(self, from_address):
        self.driver.find_element(*self.from_field).send_keys(from_address)

    def set_to(self, to_address):
        self.driver.find_element(*self.to_field).send_keys(to_address)

    def get_from(self):
        return self.driver.find_element(*self.from_field).get_property('value')

    def get_to(self):
        return self.driver.find_element(*self.to_field).get_property('value')

class TestUrbanRoutes:

    driver = None

    @classmethod
    def setup_class(cls):
        options = Options()
        options.set_capability("goog:loggingPrefs", {'performance': 'ALL'})
        cls.driver = webdriver.Chrome(options=options)

    @classmethod
    def teardown_class(cls):
        cls.driver.quit()

#Prueba 1
    def test_set_route(self):
        self.driver.get(data.urban_routes_url)
        routes_page = UrbanRoutesPage(self.driver)

        wait = WebDriverWait(self.driver, 10)
        wait.until(EC.presence_of_element_located(UrbanRoutesPage.from_field))
        wait.until(EC.presence_of_element_located(UrbanRoutesPage.to_field))

        address_from = data.address_from
        address_to = data.address_to
        routes_page.set_from(address_from)
        routes_page.set_to(address_to)
        assert routes_page.get_from() == address_from
        assert routes_page.get_to() == address_to

# Prueba 2
    def test_select_comfort_tariff(self):
        self.driver.get(data.urban_routes_url)
        comfort_tariff = (By.XPATH, '//div[@class="tcard"][.//div[@class="tcard-title" and text()="Comfort"]]//button')
        self.driver.find_element(*comfort_tariff).click()

#Prueba 3
    def test_set_phone_number(self):
        wait = WebDriverWait(self.driver, 10)

        def click_element(xpath):
            el = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            try:
                el.click()
            except:
                self.driver.execute_script("arguments[0].click();", el)

        # 1) Abrir modal de teléfono
        click_element('//div[text()="Número de teléfono"]')

        # 2) Ingresar número de teléfono
        phone_input = wait.until(lambda d: next(
            inp for inp in d.find_elements(By.TAG_NAME, "input") if inp.is_displayed() and inp.is_enabled()))
        phone_input.clear()
        phone_input.send_keys(data.phone_number)
        assert phone_input.get_attribute("value") == data.phone_number

        # 3) Click en siguiente
        click_element('//button[text()="Siguiente"]')

        # 4) Ingresar código (aquí puedes usar un código fijo o un método que lo recupere)
        code_input = wait.until(EC.visibility_of_element_located((By.ID, "code")))
        test_code = "1234"  # O reemplaza por tu función para obtener el código real
        code_input.clear()
        code_input.send_keys(test_code)
        assert code_input.get_attribute("value") == test_code

        # 5) Confirmar código
        click_element('//button[text()="Confirmar"]')

    # Cerrar el navegador
    @classmethod
    def teardown_class(cls):
        cls.driver.quit()