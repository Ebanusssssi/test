import streamlit as st
import cv2
import numpy as np
import zipfile
import os

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
def process_zip(input_zip, output_folder, bg_color):
    try:
        # Создаем временную папку для хранения обработанных изображений
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        
        # Распаковываем архив во временную папку
        with zipfile.ZipFile(input_zip, 'r') as zip_ref:
            zip_ref.extractall(output_folder)
        
        # Создаем новый архив для обработанных изображений
        output_zip = os.path.join(output_folder, 'processed_images.zip')
        with zipfile.ZipFile(output_zip, 'w') as zip_ref:
            # Проходим по всем файлам и папкам в извлеченной структуре
            for root, dirs, files in os.walk(output_folder):
                for filename in files:
                    file_path = os.path.join(root, filename)
                    
                    # Пропускаем если это не изображение
                    if not file_path.lower().endswith(('jpg', 'jpeg', 'png')):
                        continue
                    
                    # Меняем фон на выбранный цвет
                    output_image_path = os.path.join(output_folder, f'processed_{filename}')
                    error = change_background(file_path, output_image_path, bg_color)
                    
                    if error:
                        st.error(error)
                        continue
                    
                    # Добавляем обработанное изображение в архив
                    zip_ref.write(output_image_path, os.path.relpath(output_image_path, output_folder))
                    # Удаляем временный обработанный файл
                    os.remove(output_image_path)
        
        return output_zip  # Возвращаем путь к архиву с обработанными изображениями
    except Exception as e:
        return f"Ошибка при обработке архива: {e}"

# Основная часть программы для Streamlit
def main():
    st.title('Изменение фона изображений')
    
    # Ввод цвета для фона
    st.subheader("Введите цвет фона (RGB):")
    # Создаем три отдельных слайдера для RGB
    r = st.slider("Красный (R)", 0, 255, 0, step=1)
    g = st.slider("Зеленый (G)", 0, 255, 0, step=1)
    b = st.slider("Синий (B)", 0, 255, 255, step=1)

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
            output_folder = "output_folder"
            
            result = process_zip("uploaded.zip", output_folder, bg_color)
            
            if isinstance(result, str) and result.endswith(".zip"):
                st.success("Обработка завершена! Скачать архив с изображениями:")
                with open(result, 'rb') as f:
                    st.download_button('Скачать архив', f, file_name='processed_images.zip')
            else:
                st.error(result)

if __name__ == "__main__":
    main()
