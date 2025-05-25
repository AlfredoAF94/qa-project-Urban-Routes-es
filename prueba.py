class TestUrbanRoutes:

    driver = None

    @classmethod
    def setup_class(cls):
        # no lo modifiques, ya que necesitamos un registro adicional habilitado para recuperar el código de confirmación del teléfono
        from selenium.webdriver import DesiredCapabilities
        capabilities = DesiredCapabilities.CHROME
        capabilities["goog:loggingPrefs"] = {'performance': 'ALL'}
        cls.driver = webdriver.Chrome(desired_capabilities=capabilities)

    # Prueba 2
    def test_select_comfort_tariff(self):
        self.driver.get(data.urban_routes_url)
        comfort_tariff = (By.XPATH, '//div[@class="tcard"][.//div[@class="tcard-title" and text()="Comfort"]]//button')
        self.driver.find_element(*comfort_tariff).click()