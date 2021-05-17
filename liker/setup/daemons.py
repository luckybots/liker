import inject
from tengi import MessagesLogger, AbuseJanitor


def create_daemon_instances():
    """
    Create instances that aren't referenced by application tree (starting from App), so they should be created
    explicitly
    :return:
    """
    inject.instance(MessagesLogger)
    inject.instance(AbuseJanitor)
