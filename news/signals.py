from django.contrib.sites.shortcuts import get_current_site
from django.db.models.signals import m2m_changed
from django.dispatch import receiver  # импортируем нужный декоратор
from django.core.mail import EmailMultiAlternatives  # импортируем класс для создания объекта письма с html
from django.template.loader import render_to_string  # импортируем функцию, которая срендерит наш html в текст

from .models import Post, PostCategory, CategorySubscribers
from NewsPaper.settings import DEFAULT_FROM_EMAIL  # для почтового ящика по умолчанию


@receiver(m2m_changed, sender=PostCategory)
def notify_post_create(sender, instance, action, **kwargs):
    """  С помощью данного метода мы создаем "post_add" который отправляется после добавления одного или нескольких
    объектов. Далее с помощью instance - экземпляр, чье отношение «многие-ко-многим» обновляется, мы можем получить
    все посты всех категорий. С помощью фильтрации получаем категорию на которую подписан пользователь. Формируем
    тему и сообщение с помощью EmailMultiAlternatives, так же получаем список e-mail пользователей для рассылки.
    """
    if action == 'post_add':
        for cat in instance.post_category.all():
            for subscribe in CategorySubscribers.objects.filter(category=cat):

                msg = EmailMultiAlternatives(
                    subject=instance.headline,
                    body=instance.post_text,
                    from_email=DEFAULT_FROM_EMAIL,
                    to=[subscribe.subscriber_user.email],
                )

                " Получения ссылки поста в теле письма "
                full_url = ''.join(['http://', get_current_site(None).domain, ':8001'])

                html_content = render_to_string(
                    'post_create.html',
                    {
                        'posts': instance.post_text,
                        'recipient': subscribe.subscriber_user.email,
                        'category_name': subscribe.category,
                        'subscriber_user': subscribe.subscriber_user,
                        'pk_id': instance.pk,
                        'date': instance.create_date,
                        'current_site': full_url,
                    },
                )

                msg.attach_alternative(html_content, "text/html")
                msg.send()

                # print(f'{instance.headline} {instance.post_text}')
                # print('Уведомление отослано подписчику ',
                #       subscribe.subscriber_user, 'на почту',
                #       subscribe.subscriber_user.email, ' на тему ', subscribe.category)


def collect_subscribers(category):
    """ Перебрать всех подписчиков в таблице категорий, извлечь их электронную почту
     и сформировать список получателей электронной почты """
    email_recipients = []
    for user in category.subscribers.all():
        email_recipients.append(user.email)

    return email_recipients


def send_emails(post_object, **kwargs):
    """ Функция подготовки всех постов для передачи любых переменных в шаблон HTML который будет сформирован
    render_to_string и отправлен на почту подписчикам """
    html = render_to_string(
        kwargs['template'],
        {
            # передаем в шаблон любые переменные
            'category_object': kwargs['category_object'],
            # передаем в шаблон любые переменные
            'post_object': post_object,
            # передаем в шаблон domain
            'current_url': ''.join(['http://', get_current_site(None).domain, ':8001'])
        },
    )

    msg = EmailMultiAlternatives(
        # Тема сообщения
        subject=kwargs['email_subject'],
        # Вставляем от кого рассылка
        from_email=DEFAULT_FROM_EMAIL,
        # отправляем всем подписчикам из списка рассылку
        to=kwargs['email_recipients']
    )

    msg.attach_alternative(html, 'text/html')
    msg.send(fail_silently=False)
