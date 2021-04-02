# noinspection PyUnresolvedReferences
from liker.setup import logs  # has import side effect
import inject
from tengine import App

from liker.setup.dependencies import bind_app_dependencies
from liker.setup.daemons import create_daemon_instances


@inject.autoparams()
def main():
    inject.configure(bind_app_dependencies)
    create_daemon_instances()

    app = inject.instance(App)
    app.run()


if __name__ == '__main__':
    main()
