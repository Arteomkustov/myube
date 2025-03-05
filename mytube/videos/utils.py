import django
import ffmpeg
import multiprocessing
import os
import tempfile
import time
import speech_recognition as sr

from pydub import AudioSegment
from concurrent.futures import ThreadPoolExecutor

from whoosh.index import create_in, open_dir
from whoosh.fields import Schema, TEXT, ID
from whoosh.qparser import MultifieldParser
from .models import Videos, Channel, VideoView
from django.utils import timezone

# from .models import Videos


def preprocess_video(input_path, temp_path, resolution):
    try:
        print(f"Предварительная обработка {input_path} в {temp_path} с разрешением {resolution} с использованием GPU.")
        ffmpeg.input(input_path).output(
            temp_path,
            vcodec='h264_nvenc',  # Использование кодека NVENC для NVIDIA видеокарт
            vf=f'scale={resolution}',
            b='500k',
            acodec='aac',  # Использование кодека AAC для аудио
            threads=4
        ).run(overwrite_output=True)
        print(f"Успешно обработано {input_path} в {temp_path}")
    except ffmpeg.Error as e:
        print(f"Ошибка при обработке {input_path} в {temp_path}: {e}")
        print(e.stderr.decode())  # Показать подробную ошибку FFmpeg

def convert_to_h264_nvenc(temp_path, output_path):
    try:
        print(f"Конвертация {temp_path} в {output_path} в формат H.264 с использованием GPU.")
        ffmpeg.input(temp_path).output(
            output_path,
            vcodec='h264_nvenc',  # Использование кодека NVENC для NVIDIA видеокарт
            acodec='aac',
            threads=4
        ).run(overwrite_output=True)
        print(f"Успешно конвертировано {temp_path} в {output_path}")
    except ffmpeg.Error as e:
        print(f"Ошибка при конвертации {temp_path} в {output_path}: {e}")
        print(e.stderr.decode())  # Показать подробную ошибку FFmpeg

def process_video(input_path, resolutions, output_videos):
    for res, output_path in output_videos.items():
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        temp_path = temp_file.name
        temp_file.close()

        preprocess_video(input_path, temp_path, resolutions[res])
        convert_to_h264_nvenc(temp_path, output_path)

    print("Обработка видео завершена.")


def file_existence_checker(output_videos):
    while True:
        all_files_exist = all([os.path.exists(output_path) for output_path in output_videos.values()])
        if all_files_exist:
            print("Все выходные файлы созданы. Завершение программы.")
            break
        time.sleep(1)  # Проверка каждые 1 секунду


def convert(filename):
    base_path = __file__[:-16] + '\media\\videos\\'
    input_video = base_path + filename
    output_path = base_path
    output_videos = {
        '720p': output_path + filename + '_' + "output_video_720p.mp4",
        '144p': output_path + filename + '_' + "output_video_144p.mp4",
        '360p': output_path + filename + '_' + "output_video_360p.mp4"
    }
    resolutions = {
        '720p': '1280:720',
        '144p': '256:144',
        '360p': '640:360'
    }

    #os.mkdir(output_path)

    print(input_video, output_videos['720p'], 11)

    process_video(input_video, resolutions, output_videos)

    print(base_path + filename)
    print('Converted')
    return ['videos/' + filename + '_' + "output_video_144p.mp4",
            'videos/' + filename + '_' + "output_video_360p.mp4",
            'videos/' + filename + '_' + "output_video_720p.mp4"
            ]


def extract_audio(input_path, output_path):
    try:
        print(f"Извлечение звуковой дорожки из {input_path} в {output_path}.")
        ffmpeg.input(input_path).output(output_path, q=0, map='a').run(overwrite_output=True)
        print(f"Успешно извлечена звуковая дорожка в {output_path}.")
    except ffmpeg.Error as e:
        print(f"Ошибка при извлечении звуковой дорожки из {input_path}: {e}")
        print(e.stderr.decode())


def recognize_chunk(recognizer, chunk_filename, start_time, end_time, language="ru-RU"):
    try:
        with sr.AudioFile(chunk_filename) as source:
            audio_listened = recognizer.record(source)
            recognized_text = recognizer.recognize_google(audio_listened, language=language)
            print(f"Сгенерирован кусок с {start_time} до {end_time}: {recognized_text}")
            return start_time, end_time, recognized_text
    except sr.UnknownValueError:
        print(f"Не удалось распознать кусок с {start_time} до {end_time}")
        return start_time, end_time, ""
    except sr.RequestError as e:
        print(f"Ошибка запроса при распознавании куска с {start_time} до {end_time}: {e}")
        return start_time, end_time, ""


def generate_subtitles(audio_path, subtitle_path, c_p):
    try:
        print(f"Генерация субтитров для {audio_path} на русском языке.")
        recognizer = sr.Recognizer()
        audio = AudioSegment.from_wav(audio_path)
        chunk_length_ms = 5000  # 5 секунд
        audio_chunks = [audio[i:i+chunk_length_ms] for i in range(0, len(audio), chunk_length_ms)]

        with ThreadPoolExecutor() as executor:
            futures = []
            for i, chunk in enumerate(audio_chunks):
                start_time = i * chunk_length_ms
                end_time = start_time + len(chunk)
                chunk_filename = f"chunk{i}_{c_p}.wav"
                chunk.export(chunk_filename, format="wav")
                futures.append(executor.submit(recognize_chunk, recognizer, chunk_filename, start_time, end_time))

            results = []
            for future in futures:
                results.append(future.result())

            results.sort()  # Сортируем результаты по времени начала куска

            with open(subtitle_path, 'w', encoding='utf-8') as subtitle_file:
                subtitle_file.write("WEBVTT\n\n")
                for start_time, end_time, text in results:
                    if text:
                        start = f"{start_time//3600000:02}:{(start_time//60000)%60:02}:{(start_time//1000)%60:02}.{start_time%1000:03}"
                        end = f"{end_time//3600000:02}:{(end_time//60000)%60:02}:{(end_time//1000)%60:02}.{end_time%1000:03}"
                        subtitle_file.write(f"{start} --> {end}\n{text}\n\n")

            # Удаляем временные файлы chunk
            for i, _ in enumerate(audio_chunks):
                os.remove(f"chunk{i}_{c_p}.wav")

        print(f"Субтитры успешно сгенерированы в {subtitle_path}.")
    except Exception as e:
        print(f"Ошибка при генерации субтитров для {audio_path}: {e}")


def generate_s(filename):
    base_path = __file__[:-16] + '\media\\videos\\'
    input_video = base_path + filename
    output_path = base_path
    output_audio = output_path + filename + '_' + "output_audio.wav"
    output_file = output_path + filename + '_' + "output_subtitles.vtt"


    #print(input_video,output_audio, 11)


    #print(base_path + filename)
    extract_audio(input_video, output_audio)
    generate_subtitles(output_audio, output_file, filename)

    #print('Converted')
    return 'videos/' + filename + '_' + "output_subtitles.vtt"


def process_and_save_video(input_path, original):
    print(input_path[7:], 10)
    output_path = convert(input_path[7:])
    output_subtitles_path = generate_s(input_path[7:])
    original.converted_video_file_144 = output_path[0]
    original.converted_video_file_380 = output_path[1]
    original.converted_video_file_720 = output_path[2]
    original.subtitles = output_subtitles_path
    original.ready = True
    original.save()


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


if __name__ == '__main__':
    print(generate_s("output_video_144p.mp4"))
    input_video = "output_video_144p.mp4"
    output_audio = "output_audio.wav"
    subtitle_file = "subtitles.vtt"

    # extract_audio(input_video, output_audio)
    # generate_subtitles(output_audio, subtitle_file)
    # convert('test3.mp4')


def create_search_index():
    if not os.path.exists("index"):
        os.mkdir("index")

    schema = Schema(
        title=TEXT(stored=True),
        overview=TEXT(stored=True),
        slug=ID(stored=True, unique=True),
        type=TEXT(stored=True)
    )

    ix = create_in("index", schema)
    writer = ix.writer()

    for video in Videos.objects.all():
        writer.add_document(
            title=video.title,
            overview=video.overview,
            slug=video.slug,
            type="video"
        )

    for channel in Channel.objects.all():
        writer.add_document(
            title=channel.name,
            overview=channel.overview,
            slug=channel.slug,
            type="channel"
        )

    writer.commit()


def search(query):
    create_search_index()
    ix = open_dir("index")
    with ix.searcher() as searcher:
        parser = MultifieldParser(["title", "overview"], ix.schema)
        query = parser.parse(query)
        results = searcher.search(query, limit=None)

        videos = []
        channels = []

        for result in results:
            if result['type'] == 'video':
                videos.append(Videos.objects.get(slug=result['slug']))
            elif result['type'] == 'channel':
                channels.append(Channel.objects.get(slug=result['slug']))

        return videos, channels



def add_video_view(request, video):
    ip_address = request.META.get('REMOTE_ADDR')
    if request.user.is_authenticated:
        print(1)
        VideoView.objects.create(user=request.user, video=video, ip_address=ip_address, viewed_at=timezone.now())
    else:
        # Хранение информации о просмотре в файлах куки

        pass  # Здесь добавьте логику для хранения информации о просмотре в файлах куки


def get_video_views(video):
    return VideoView.objects.filter(video=video)


from django.db.models import Count
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
import pandas as pd
import random


def get_random_videos():
    all_videos = list(Videos.objects.all())
    random.shuffle(all_videos)
    return all_videos[:20]  # Возвращаем 10 случайных видео

def get_collaborative_recommendations(user):
    user_viewed_videos = VideoView.objects.filter(user=user).values_list('video_id', flat=True)

    similar_users = VideoView.objects.filter(video_id__in=user_viewed_videos).exclude(user=user).values(
        'user_id').annotate(count=Count('id')).order_by('-count')

    similar_users_ids = [user['user_id'] for user in similar_users]

    recommended_videos = VideoView.objects.filter(user_id__in=similar_users_ids).exclude(
        video_id__in=user_viewed_videos).values_list('video_id', flat=True)

    return Videos.objects.filter(id__in=recommended_videos)

def home_recomendation(user):
    r = get_collaborative_recommendations(user)
    if not r.exists():
        r = get_random_videos()

    return r


def get_content_based_recommendations(video):
    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(Videos.objects.values_list('overview', flat=True))

    cosine_sim = linear_kernel(tfidf_matrix, tfidf_matrix)

    video_indices = pd.Series(Videos.objects.values_list('id', flat=True))
    idx = video_indices[video_indices == video.id].index[0]

    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_scores = sim_scores[1:11]  # Топ-10 рекомендаций

    video_indices = [i[0] for i in sim_scores]

    return Videos.objects.filter(id__in=video_indices)





def get_hybrid_recommendations(user, video):
    collaborative_recommendations = get_collaborative_recommendations(user)
    content_based_recommendations = get_content_based_recommendations(video)

    print(collaborative_recommendations)

    recommendations = collaborative_recommendations | content_based_recommendations
    #recommendations = recommendations.distinct()  # Убираем дубли

    if not recommendations.exists():
        recommendations = get_random_videos()

    return recommendations



