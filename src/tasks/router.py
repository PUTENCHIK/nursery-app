from fastapi import APIRouter, Depends

from src.database import DBSession
from src.dependencies import get_db_session, get_logger

from src.exceptions.TaskExceptions import *
from src.exceptions.ResponseExceptions import *

from src.users.router import get_user
from src.users.schemas.UserAuth import UserAuth

from src.collars.crud import get_exploit

from src.tasks.schemas.TaskBase import TaskBase
from src.tasks.schemas.TaskAdd import TaskAdd
from src.tasks.schemas.Task import Task
from src.tasks.schemas.ResponseBase import ResponseBase
from src.tasks.schemas.ResponseAdd import ResponseAdd
from src.tasks.schemas.Response import Response


from src.tasks.crud import (
    add_task as add_db_task,
    add_response as add_db_response,
    confirm_response as confirm_db_response,
    remove_task as remove_db_task,
    remove_response as remove_db_response,
    get_task as get_db_task,
    get_user_tasks,
    get_response as get_db_response,
)

tasks_router = APIRouter()
router_name = "/tasks"
logger = get_logger(router_name)


@tasks_router.post(f"{router_name}/add_task", response_model=TaskBase)
def add_task(task: TaskAdd, user: UserAuth, db: DBSession = Depends(get_db_session)):
    """
    Checks task schema and if it's valid, will add task to db.

    :param task: schema which contains collar_id and text of task
    :type task: TaskAdd

    :param user: schema which contains user's token for authentication
    :type user: UserAuth

    :param db: session for connecting to db
    :type db: sessionmaker

    :return: id of new task
    :rtype: TaskBase

    :raises UnlinkedCollar
    :raises TooShortText
    """
    logger.add_info(f"Called {router_name}/add_task")

    db_user = get_user(token=user.user_token, db=db)
    db_exploit = get_exploit(db, collar_id=task.collar_id)

    if db_exploit is None:
        logger.add_error(f"UnlinkedCollar exception raised: collar_id = '{task.collar_id}'")
        raise UnlinkedCollar(task.collar_id)

    if len(task.text) < 11:
        logger.add_error(f"TooShortText exception raised")
        raise TooShortText()

    return add_db_task(db, task, db_user.id)


@tasks_router.post(f"{router_name}/add_response", response_model=ResponseBase)
def add_response(response: ResponseAdd, user: UserAuth, db: DBSession = Depends(get_db_session)):
    """
    Checks response schema and if it's valid, will add response to db.

    :param response: schema which contains task_id and path to confirming image
    :type response: ResponseAdd

    :param user: schema which contains user's token for authentication
    :type user: UserAuth

    :param db: session for connecting to db
    :type db: sessionmaker

    :return: id of new response
    :rtype: ResponseBase

    :raises UserIsAuthorOfTask
    """
    logger.add_info(f"Called {router_name}/add_response")

    db_user = get_user(token=user.user_token, db=db)
    db_task = get_task(response.task_id, db)

    if db_user.id == db_task.author_id:
        logger.add_error(f"UserIsAuthorOfTask exception raised: task_id = '{db_task.id}'")
        raise UserIsAuthorOfTask(db_task.id)

    return add_db_response(db, response, db_user.id)


@tasks_router.post(f"{router_name}/confirm_response", response_model=bool)
def confirm_response(response: ResponseBase, user: UserAuth, db: DBSession = Depends(get_db_session)):
    """
    If response exists and user is author of linked task and task hasn't had other confirmed responses,
    response will become confirmed.

    :param response: schema which contains response's id
    :type response: ResponseBase

    :param user: schema which contains user's token for authentication
    :type user: UserAuth

    :param db: session for connecting to db
    :type db: sessionmaker

    :return: true if response was confirmed
    :rtype: bool

    :raises UserIsNotAuthor
    :raises ResponseAlreadyConfirmed
    :raises TaskHasConfirmedResponse
    """
    logger.add_info(f"Called {router_name}/confirm_response")

    db_user = get_user(token=user.user_token, db=db)
    db_response = get_response(response.id, db)
    db_task = get_task(db_response.task_id, db)

    if db_user.id != db_task.author_id:
        logger.add_error(
            f"UserIsNotAuthor exception raised: author_id = '{db_task.author_id}', "
            f"response_id = '{response.id}', "
            f"task_id = '{db_task.id}'"
        )
        raise UserIsNotAuthor(db_task.author_id, response.id, db_task.id)

    db_confirmed = get_db_response(db, task_id=db_task.id, is_confirmed=True)
    if db_confirmed is not None:
        if db_confirmed.id == response.id:
            logger.add_error(f"ResponseAlreadyConfirmed exception raised: response_id = '{response.id}'")
            raise ResponseAlreadyConfirmed(response.id)
        else:
            logger.add_error(
                f"TaskHasConfirmedResponse exception raised: task_id = '{db_task.id}', "
                f"response_id = '{db_confirmed.id}'"
            )
            raise TaskHasConfirmedResponse(db_task.id, db_confirmed.id)

    return confirm_db_response(db, db_response)


@tasks_router.post(f"{router_name}/remove_task", response_model=bool)
def remove_task(task: TaskBase, user: UserAuth, db: DBSession = Depends(get_db_session)):
    """
    If task exists and user is author of task and task hasn't responses, task will be noted as deleted.

    :param task: schema with task's id
    :type task: TaskBase

    :param user: schema which contains user's token for authentication
    :type user: UserAuth

    :param db: session for connecting to db
    :type db: sessionmaker

    :return: true if task was deleted
    :rtype: bool

    :raises NotUsersTask
    :raises TaskHasResponses
    """
    logger.add_info(f"Called {router_name}/remove_task")

    db_user = get_user(token=user.user_token, db=db)
    db_task = get_task(task.id, db)

    if db_user.id != db_task.author_id:
        logger.add_error(f"NotUsersTask exception raised: task_id = '{task.id}'")
        raise NotUsersTask(task.id)

    db_response = get_db_response(db, task_id=task.id)
    if db_response is not None:
        logger.add_error(f"TaskHasResponses exception raised: task_id = '{task.id}'")
        raise TaskHasResponses(task.id)

    return remove_db_task(db, db_task)


@tasks_router.post(f"{router_name}/remove_response", response_model=bool)
def remove_response(response: ResponseBase, user: UserAuth, db: DBSession = Depends(get_db_session)):
    """
    If response exists and user is creator of response, response will be noted as deleted.

    :param response: schema with response's id
    :type response: ResponseBase

    :param user: schema which contains user's token for authentication
    :type user: UserAuth

    :param db: session for connecting to db
    :type db: sessionmaker

    :return: true if response was deleted
    :rtype: bool

    :raises NotUsersResponse
    """
    logger.add_info(f"Called {router_name}/remove_response")

    db_user = get_user(token=user.user_token, db=db)
    db_response = get_response(response.id, db)

    if db_user.id != db_response.author_id:
        logger.add_error(f"NotUsersResponse exception raised: response_id = '{response.id}'")
        raise NotUsersResponse(response.id)

    return remove_db_response(db, db_response)


@tasks_router.get(f"{router_name}/get_task", response_model=Task)
def get_task(task_id: int, db: DBSession = Depends(get_db_session)):
    """
    Gets database task with gotten id and if it isn't None, returns schema with id, collar's id and text of task.

    :param task_id: task's id
    :type: int

    :param db: session for connecting to db
    :type db: sessionmaker

    :return: task's schema with its data
    :rtype: Task

    :raises NoTask
    """
    logger.add_info(f"Called {router_name}/get_task")

    db_task = get_db_task(db, task_id)

    if db_task is None:
        logger.add_error(f"NoTask exception raised: task_id = '{task_id}'")
        raise NoTask(task_id)

    return db_task


@tasks_router.get(f"{router_name}/get_tasks", response_model=list[Task])
def get_tasks(author_id: int, db: DBSession = Depends(get_db_session)):
    """
    Returns list of user's tasks.

    :param author_id: id of user who is creator of tasks
    :type: int

    :param db: session for connecting to db
    :type db: sessionmaker

    :return: list of schemas class Task
    :rtype: list[Task]
    """
    logger.add_info(f"Called {router_name}/get_tasks")

    return get_user_tasks(db, author_id)


@tasks_router.get(f"{router_name}/get_response", response_model=Response)
def get_response(response_id: int, db: DBSession = Depends(get_db_session)):
    """
    Gets database response with gotten id and if it isn't None, returns schema with id, task's id and path of image.

    :param response_id: response's id
    :type: int

    :param db: session for connecting to db
    :type db: sessionmaker

    :return: response's schema with its data
    :rtype: Response

    :raises NoResponse
    """
    logger.add_info(f"Called {router_name}/get_response")

    db_response = get_db_response(db, response_id=response_id)

    if db_response is None:
        logger.add_error(f"NoResponse exception raised: response_id = '{response_id}'")
        raise NoResponse(response_id)

    return db_response
