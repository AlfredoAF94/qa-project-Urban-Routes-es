#main.py

import data
import time
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

#Prueba 1: Agregar dirección
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

# Prueba 2: Seleccionar tarifa "Comfort"
    def test_select_comfort_tariff(self):
        wait = WebDriverWait(self.driver, 10)

        # Paso 1: Asegurar que estamos en modo Flash
        wait.until(EC.presence_of_element_located((By.XPATH, '//div[@class="mode active" and text()="Flash"]')))

        # Paso 2: Clic en el ícono del taxi
        taxi_icon = wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//img[contains(@src, "taxi-active")]')
        ))
        taxi_icon.click()

        # Paso 3: Esperar y dar clic al botón "Pedir un taxi"
        pedir_taxi_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//button[contains(@class, "button round") and text()="Pedir un taxi"]')
        ))
        pedir_taxi_btn.click()

        # Paso 4: Seleccionar la tarjeta Comfort
        comfort_card = wait.until(EC.element_to_be_clickable((
            By.XPATH,
            '//div[contains(@class, "tcard") and .//div[contains(text(), "Comfort")]]'
        )))
        comfort_card.click()

    # Prueba 3: Añadir número de teléfono
    def test_set_phone_number(self):
        wait = WebDriverWait(self.driver, 10)
        routes_page = UrbanRoutesPage(self.driver)

        # Paso 1: Localizar el trigger “Número de teléfono” y hacer clic
        toggle = wait.until(EC.element_to_be_clickable((
            By.XPATH,
            '//div[text()="Número de teléfono"]'
        )))
        try:
            toggle.click()
        except:
            self.driver.execute_script("arguments[0].click();", toggle)

        # Paso 2: Abrir el modal de teléfono
        toggle = wait.until(EC.element_to_be_clickable((
            By.XPATH, '//div[text()="Número de teléfono"]'
        )))
        try:
            toggle.click()
        except:
            self.driver.execute_script("arguments[0].click();", toggle)

        # Paso 3: Buscar cualquier <input> visible y habilitado
        phone_inputs = WebDriverWait(self.driver, 10).until(
            lambda d: [
                          inp for inp in d.find_elements(By.TAG_NAME, "input")
                          if inp.is_displayed() and inp.is_enabled()
                      ] or False
        )
        phone_input = phone_inputs[0]

        # Paso 4: Escribir y verificar
        phone_input.clear()
        phone_input.send_keys(data.phone_number)
        assert phone_input.get_attribute("value") == data.phone_number

        # Paso 5: Hacer clic en el botón "Siguiente"
        next_btn = wait.until(EC.element_to_be_clickable((
            By.XPATH, '//button[text()="Siguiente"]'
        )))
        next_btn.click()

        # Paso 6: Esperar input del código
        code_input = wait.until(EC.visibility_of_element_located((
            By.ID, "code"
        )))

        # Paso 7: Obtener código real con retrieve_phone_code()
        test_code = retrieve_phone_code(self.driver)

        code_input.clear()
        code_input.send_keys(test_code)
        assert code_input.get_attribute("value") == test_code

        # Paso 8: Clic en "Confirmar"
        confirm_btn = wait.until(EC.element_to_be_clickable((
            By.XPATH, '//button[text()="Confirmar"]'
        )))
        confirm_btn.click()

    # Prueba 4: Agregar una tarjeta de crédito
    def test_add_credit_card(self):
        wait = WebDriverWait(self.driver, 10)

        # Paso 1: Esperar a que desaparezca el overlay (pantalla de carga o bloqueo)
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.overlay")))

        # Paso 2: Esperar a que el botón principal de "Método de pago" esté presente
        pay_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div.pp-button.filled')))

        # Paso 3: Forzar clic con JS en el botón de "Método de pago"
        self.driver.execute_script("arguments[0].click();", pay_button)

        # Paso 4: Esperar que aparezca el título "Agregar tarjeta" (se abrió la ventana)
        add_card_option = wait.until(EC.element_to_be_clickable((
            By.XPATH, '//div[contains(@class, "pp-row") and .//div[text()="Agregar tarjeta"]]'
        )))

        # Paso 5: Dar clic en "Agregar tarjeta"
        try:
            add_card_option.click()
        except:
            self.driver.execute_script("arguments[0].click();", add_card_option)

        # Paso 6: Esperar que el input del número de tarjeta esté visible y habilitado
        number_input = wait.until(EC.element_to_be_clickable((By.ID, "number")))
        number_input.click()  # Clic explícito
        number_input.clear()
        number_input.send_keys(data.card_number)

        # Paso 7: Esperar que el input del CVV sea visible (aunque no clickeable)
        cvv_input = wait.until(EC.visibility_of_element_located((By.ID, "code")))
        cvv_input.clear()
        cvv_input.send_keys(data.card_code)

    # Cerrar el navegador
    @classmethod
    def teardown_class(cls):
        time.sleep(5)
        cls.driver.quit()
