from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import mysql.connector
import time
import re

# Configuración de la base de datos MySQL
def conectar():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="masonlinescrap"
    )

# Store procedure para insertar o actualizar artículos
def insertar(cursor, nombre, precio):
    cursor.callproc('Sp_registrar_Producto', (nombre, precio))

# Función para convertir el precio al formato adecuado
def parsear_precio(precio):
    precio = re.sub(r'[^0-9,]', '', precio)  # Elimina todo excepto números y comas
    # Reemplazar la coma por un punto para convertir el valor decimal
    precio = precio.replace(',', '.')
    return float(precio)

# Configurar el controlador de Selenium
driver = webdriver.Chrome()
esp = WebDriverWait(driver, 10)

# Conjunto para almacenar los nombres de los artículos ya guardados
productos_yaGuardados = set()

urls = [
    "https://www.masonline.com.ar/3434?page={}&map=productClusterIds",
    "https://www.masonline.com.ar/3455?page={}&map=productClusterIds",
    "https://www.masonline.com.ar/272?page={}&map=productClusterIds",
    "https://www.masonline.com.ar/273?page={}&map=productClusterIds",
    "https://www.masonline.com.ar/3435?page={}&map=productClusterIds",
    "https://www.masonline.com.ar/3436?page={}&map=productClusterIds",
    "https://www.masonline.com.ar/262?page={}&map=productClusterIds",
    "https://www.masonline.com.ar/275?page={}&map=productClusterIds",
    "https://www.masonline.com.ar/3437?page={}&map=productClusterIds",
    "https://www.masonline.com.ar/3438?page={}&map=productClusterIds"
]

for base_url in urls:
    # Comienza en la página
    page_number = 1
    
    while True:
        url = base_url.format(page_number)
        driver.get(url)
        time.sleep(3)
        
        # Obtener la altura total de la página
        last_height = driver.execute_script("return document.body.scrollHeight")
    
        while True:
            # Desplazarse hacia abajo en pasos pequeños
            for i in range(1, 6):  # Ajusta el rango según lo rápido que quieras que sea el desplazamiento
                driver.execute_script(f"window.scrollTo(0, {last_height * i / 5});")
                time.sleep(0.5)  # Espera un poco entre desplazamientos
        
            # Espera a que se cargue el contenido
            time.sleep(2)  # Ajusta el tiempo según la velocidad de carga de la página
        
            # Calcula la nueva altura de la página después del scroll
            new_height = driver.execute_script("return document.body.scrollHeight")
    
            # Si no hay más contenido para cargar, rompe el bucle
            if new_height == last_height:
                break
        
            last_height = new_height
            
        
        # Conectar a la base de datos antes del bucle
        conexion = conectar()
        cursor = conexion.cursor()
    
    
        try:
            # Esperar a que el contenedor principal de artículos esté presente
            contenedor = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'vtex-search-result-3-x-gallery.flex.flex-row.flex-wrap.items-stretch.bn.ph1.na4.pl9-l'))
            )
    
            # Obtener el contenido de la página y parsear con BeautifulSoup
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            contenedor = soup.find('div', class_='vtex-search-result-3-x-gallery flex flex-row flex-wrap items-stretch bn ph1 na4 pl9-l')
    
            # Iterar sobre cada artículo en la galería
            if contenedor:
                productos = contenedor.find_all('div', class_='vtex-search-result-3-x-galleryItem vtex-search-result-3-x-galleryItem--small pa4')
                
                for producto in productos:
                    # Obtener el nombre del artículo
                    nombre = WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.CLASS_NAME, 'vtex-product-summary-2-x-productBrand.vtex-product-summary-2-x-brandName.t-body'))
                    )
                    nombre = producto.find('span', class_='vtex-product-summary-2-x-productBrand vtex-product-summary-2-x-brandName t-body').get_text(strip=True)
                        
                    # Verificar si el artículo ya fue guardado
                    if nombre in productos_yaGuardados:
                        continue
                        
                    # Intentar encontrar el precio
                    precio = WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.CLASS_NAME, 'mt4.valtech-gdn-dynamic-product-0-x-weighableListPrice'))
                    )
                    precio = producto.find('span', class_='mt4 valtech-gdn-dynamic-product-0-x-weighableListPrice')
                    if not precio:
                        precio = WebDriverWait(driver, 15).until(
                            EC.presence_of_element_located((By.CLASS_NAME, 'valtech-gdn-dynamic-product-0-x-dynamicProductPrice.mb4'))
                        )
                        precio = producto.find('div', class_='valtech-gdn-dynamic-product-0-x-dynamicProductPrice mb4')
                        
                    if precio:
                        try:
                            precio_valor = parsear_precio(precio.get_text(strip=True))
                            # Llamar al procedimiento almacenado para insertar o actualizar
                            insertar(cursor, nombre, precio_valor)
                            conexion.commit()  # Guardar cambios en la base de datos
                                
                            # Añadir el artículo al conjunto de guardados
                            productos_yaGuardados.add(nombre)
    
                        except ValueError as ve:
                            print(f"Error al parsear el precio para {nombre}: {ve}")
            
        except Exception as e:
            print("No hay mas productos para guardar")
            break  # Salir del bucle
    
        # Cerrar la conexión a la base de datos al final
        cursor.close()
        conexion.close()
        page_number += 1
    
print(f"Finalizado el recorrido hasta la página: {page_number - 1}")
driver.quit()
        