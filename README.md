# Шаг 1 создайте папку на диске C: (например myube) и откройте её в терменале.
# Шаг 2 введите git clone https://github.com/Arteomkustov/myube.git, затем cd myube
# Шаг 3 обновите драйвера на видеокарту до последней версии для работы ffmpeg (Подробнее читайте на их оффициальном сайте) и в преременной среды path для всего компьютера пропишите путь до utils\ffmpeg-master-latest-win64-gpl-shared\bin (Если вы делали первый шаг по примеру, то C:\myube\myube\utils\ffmpeg-master-latest-win64-gpl-shared\bin)
![image](https://github.com/user-attachments/assets/e2787357-41c4-48f6-9791-643265868a9b)
откройте новое окно консооли и введите ffmpeg, если всё прошло успешно, то вы увидите
![image](https://github.com/user-attachments/assets/84e38a6a-a099-4043-8aed-55907eb8ee6d)
# !!! Python должен быть версии 3.10. Перейдите в терминале в C:\myube\myube и введите python -m venv venv, затем venv\Scripts\activate.bat. Следующем шагом введите знерщт pip install -r requirements.txt
# Введите cd mytube и python manage.py runserver
# Осталось открыть в проводнике C:\myube\myube\utils\nginx-1.26.3\nginx-1.26.3, создайте папку temp, а внутри файл client_body_temp и запустить nginx.exe
# Сайт доступен по адресу 127.0.0.1 url админки /admin пароль root и других пользователей (kustovarte и softgoodcomp) user_password
