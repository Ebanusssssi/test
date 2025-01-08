import streamlit as st
import cv2
import numpy as np
import zipfile
import os
import tempfile

# Функция для размытия альфа-канала
def blur_alpha_channel(alpha_channel, blur_kernel_size=5):
    return cv2.GaussianBlur(alpha_channel, (blur_kernel_size, blur_kernel_size), 0)

# Функция для изменения фона на заданный цвет
def change_background(image_path, output_path, bg_color, transparency_threshold=180):
    try:
        # Загружаем изображение с альфа-каналом (если есть)
        img = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
        if img is None:
            return f"Ошибка: не удалось загрузить изображение {image_path}"
        
        # Проверяем, есть ли альфа-канал (прозрачность)
        if img.shape[2] == 4:  # Изображение с альфа-каналом
            # Маска для прозрачных пикселей (пиксели с альфа-каналом равным 0)
            alpha_channel = img[:, :, 3]
            transparent_mask = alpha_channel == 0

            # Размытие альфа-канала
            alpha_channel = blur_alpha_channel(alpha_channel)

            # Маска для пикселей, которые не являются полностью прозрачными
            mask = alpha_channel > transparency_threshold
            img[~mask] = np.array([bg_color[2], bg_color[1], bg_color[0], 255])  # Заполняем альфа-канал также 255

            # Преобразуем цвет фона в формат BGR (OpenCV использует BGR)
            bg_color_bgr = np.array([bg_color[2], bg_color[1], bg_color[0]])  # [B, G, R]
            
            # Заменяем прозрачные пиксели на выбранный фон
            img[transparent_mask] = np.array([bg_color_bgr[0], bg_color_bgr[1], bg_color_bgr[2], 255])  # Заполняем альфа-канал также 255
        
        else:  # Если альфа-канала нет, значит изображение имеет сплошной цвет фона
            # Переводим изображение в HSV для лучшей работы с цветами
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            
            # Определяем диапазоны для белого и черного цвета в HSV
            lower_white = np.array([0, 0, 200])
            upper_white = np.array([180, 20, 255])
            lower_black = np.array([0, 0, 0])
            upper_black = np.array([180, 0, 0])
            
            # Маски для белого и черного фона
            white_mask = cv2.inRange(hsv, lower_white, upper_white)
            black_mask = cv2.inRange(hsv, lower_black, upper_black)
            
            # Преобразуем цвет фона в формат BGR (OpenCV использует BGR)
            bg_color_bgr = np.array([bg_color[2], bg_color[1], bg_color[0]])  # [B, G, R]
            
            # Заменяем белый и черный фон на заданный цвет
            img[white_mask == 255] = bg_color_bgr
            img[black_mask == 255] = bg_color_bgr
        
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
    
    # Поля для ручного ввода значений RGB
    r_input = st.text_input("Красный (R)", "245")
    g_input = st.text_input("Зеленый (G)", "245")
    b_input = st.text_input("Синий (B)", "245")
    
    # Преобразуем ввод в целые числа, с валидацией
    try:
        r = int(r_input)
        g = int(g_input)
        b = int(b_input)
        
        if not (0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255):
            raise ValueError("Цвет должен быть в диапазоне от 0 до 255 для каждого компонента.")
        
        st.write(f"Вы выбрали цвет: RGB({r}, {g}, {b})")
    except ValueError as e:
        st.error(f"Ошибка ввода: {e}")
        return  # Прерываем выполнение, если ввод некорректен
    
    # Загрузка архива
    uploaded_file = st.file_uploader("Загрузите архив с изображениями", type=['zip'])
    
    if uploaded_file is not None
