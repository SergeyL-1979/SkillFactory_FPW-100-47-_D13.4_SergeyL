from celery import shared_task
from datetime import timedelta, date

from .models import Post
from .signals import collect_subscribers, send_emails


@shared_task
def week_email_sending():
    """ Функция отправки рассылки подписчикам собранных постов за неделю. С помощью timedelta(days=7) определяем период
    Post.objects.all() - берем все посты и создаем пустой список past_week_posts = [], в который добавим посты созданные
    за timedelta(days=7). """
    week = timedelta(days=7)
    posts = Post.objects.all()
    past_week_posts = []
    template = 'weekly_digest.html'
    email_subject = 'Your News Portal Weekly Digest'

    """ Сортируем посты от сегодняшней даты минусую по дате создания поста и если она меньше timedelta(days=7) то 
    добавляем в список past_week_posts = [] """
    for post in posts:
        time_delta = date.today() - post.create_date.date()
        if time_delta < week:
            past_week_posts.append(post)

    """ Из past_week_categories = set() делаем множество в которое будем 
    добавлять категории формируя их по постам в категориях """
    past_week_categories = set()
    for post in past_week_posts:
        for category in post.post_category.all():
            past_week_categories.add(category)

    """ Из email_recipients_set = set() делаем множество в которое будем 
        добавлять email подписчиков на категорию """
    email_recipients_set = set()
    for category in past_week_categories:
        " Запрос почтового ящика пользователя "
        get_user_emails = set(collect_subscribers(category))
        email_recipients_set.update(get_user_emails)

    """ Из раннего созданного множества email_recipients_set = set() преобразовываем его в список. Сортируем по 
    категория на которые подписаны пользователи. Формируем списки для рассылки. Создаем HTML шаблон для email и 
    делаем рассылку """
    email_recipients = list(email_recipients_set)
    for email in email_recipients:
        post_object = []
        categories = set()

        for post in past_week_posts:
            subscription = post.post_category.all().values('subscribers').filter(subscribers__email=email)
            if subscription.exists():
                post_object.append(post)
                categories.update(post.post_category.filter(subscribers__email=email))

        category_object = list(categories)

        send_emails(
            post_object,
            category_object=category_object,
            email_subject=email_subject,
            template=template,
            email_recipients=[email, ]
        )
