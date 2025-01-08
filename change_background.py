import streamlit as st
import cv2
import numpy as np
import zipfile
import os
import uuid
import shutil
import tempfile

# Функция для изменения фона на заданный цвет
def change_background(image_path, output_path, bg_color):
    try:
        # Загружаем изображение
        img = cv2.imread(image_path)
        if img is None:
            return f"Ошибка: не удалось загрузить изображение {image_path}"
        
        # Переводим изображение в HSV для лучшей работы с цветами
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        # Определяем диапазоны для белого цвета в HSV
        lower_white = np.array([0, 0, 200])
        upper_white = np.array([180, 20, 255])
        
        # Маска для белого фона
        mask = cv2.inRange(hsv, lower_white, upper_white)
        
        # Преобразуем цвет фона в формат BGR (OpenCV использует BGR)
        bg_color_bgr = np.array([bg_color[2], bg_color[1], bg_color[0]])  # [B, G, R]
        
        # Меняем белый фон на заданный цвет
        img[mask == 255] = bg_color_bgr
        
        # Сохраняем обработанное изображение
        cv2.imwrite(output_path, img)
        return None  # Успешное завершение
    except Exception as e:
        return f"Ошибка при обработке изображения {image_path}: {e}"

# Функция для работы с архивом
def process_zip(input_zip, bg_color):
    try:
        # Создаем уникальную временную папку для каждого архива
        temp_folder = tempfile.mkdtemp()

        # Распаковываем архив во временную папку
        with zipfile.ZipFile(input_zip, 'r') as zip_ref:
            zip_ref.extractall(temp_folder)

        # Создаем новый архив для обработанных изображений
        output_zip = os.path.join(temp_folder, 'processed_images.zip')
        
        with zipfile.ZipFile(output_zip, 'w') as zip_ref:
            # Проходим по всем файлам и папкам в извлеченной структуре
            for root, dirs, files in os.walk(temp_folder):
                for filename in files:
                    file_path = os.path.join(root, filename)
                    
                    # Пропускаем файлы и папки, начинающиеся с '__MACOSX' или '._'
                    if filename.startswith('__MACOSX') or filename.startswith('._'):
                        continue
                    
                    # Пропускаем если это не изображение
                    if not file_path.lower().endswith(('jpg', 'jpeg', 'png')):
                        continue
                    
                    # Меняем фон на выбранный цвет
                    output_image_path = os.path.join(temp_folder, filename)
                    error = change_background(file_path, output_image_path, bg_color)
                    
                    if error:
                        st.error(error)
                        continue
                    
                    # Добавляем обработанное изображение в архив
                    zip_ref.write(output_image_path, os.path.relpath(output_image_path, temp_folder))
        
        # Возвращаем путь к архиву с обработанными изображениями
        return output_zip

    except Exception as e:
        return f"Ошибка при обработке архива: {e}"


# Основная часть программы для Streamlit
def main():
    st.title('Изменение фона изображений')
    
    # Ввод цвета для фона
    st.subheader("Введите цвет фона (RGB):")
    r = st.slider("Красный (R)", 0, 255, 245, step=1)
    g = st.slider("Зеленый (G)", 0, 255, 245, step=1)
    b = st.slider("Синий (B)", 0, 255, 245, step=1)

    st.write(f"Вы выбрали цвет: RGB({r}, {g}, {b})")
    
    # Загрузка архива
    uploaded_file = st.file_uploader("Загрузите архив с изображениями", type=['zip'])
    
    if uploaded_file is not None:
        # Сохраняем файл
        with open("uploaded.zip", "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Кнопка для запуска обработки
        if st.button('Запустить обработку'):
            st.write("Обработка началась...")
            bg_color = [r, g, b]  # Цвет фона
            
            # Запуск функции для обработки архива
            result = process_zip("uploaded.zip", bg_color)
            
            if isinstance(result, str) and result.endswith(".zip"):
                st.success("Обработка завершена! Скачать архив с изображениями:")
                with open(result, 'rb') as f:
                    download_button = st.download_button('Скачать архив', f, file_name='BG_changed.zip')
                    
                    # Удаляем архив только после скачивания
                    if download_button:
                        os.remove(result)  # Удаляем архив после того, как пользователь скачает его
            else:
                st.error(result)

if __name__ == "__main__":
    main()
