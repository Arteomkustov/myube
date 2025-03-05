# Шаг 1 создайте папку на диске C: (например myube) и откройте её в терменале.
# Шаг 2 введите git clone https://github.com/Arteomkustov/myube.git, затем cd myube
# Шаг 3 обновите драйвера на видеокарту до последней версии для работы ffmpeg (Подробнее читайте на их оффициальном сайте) и в преременной среды path для всего компьютера пропишите путь до utils\ffmpeg-master-latest-win64-gpl-shared\bin (Если вы делали первый шаг по примеру, то C:\myube\myube\utils\ffmpeg-master-latest-win64-gpl-shared\bin)
![image](https://github.com/user-attachments/assets/e2787357-41c4-48f6-9791-643265868a9b)
откройте новое окно консооли и введите ffmpeg, если всё прошло успешно, то вы увидите
![image](https://github.com/user-attachments/assets/e1cc1a7d-18b8-470b-8a7d-54a1a1bf996c)
# !!! Python должен быть версии 3.10. Перейдите в терминале в C:\myube\myube и введите python -m venv venv, затем venv\Scripts\activate.bat. Следующем шагом введите знерщт pip install -r requirements.txt
# Введите cd mytube и python manage.py runserver
# Осталось открыть в проводнике C:\myube\myube\utils\nginx-1.26.3\nginx-1.26.3 и запустить nginx.exe
