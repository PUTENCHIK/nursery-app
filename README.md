# Приложение питомника для собак nursary-app

## Структура базы данных

`users(id, login, password, is_deleted)`\
`collars(id, code)` &emsp;// таблица ошейники (только технические характеристики)\
`exploits(id, collar_id, dog_id, start_exploit, end_exploit)` &emsp;// записи об отслеживаемых ошейниках, собаках с этими ошейниками и времеными рамками эксплуатации ошейников\
`dog(id, name, location)`\
`task_templates(id, text, id_deleted)` &emsp;// предопределённые задания для пользователей (может редактировать только админ)\
`tasks(id, author_id, dog_id, template_id, is_deleted)` &emsp;// создаваемые пользователями задания, связанные с определёнными отслеживаемыми собаками

## users_router

