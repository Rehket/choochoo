from logging import getLogger

from werkzeug.utils import redirect

from ...commands.args import JUPYTER
from ...jupyter.load import create_notebook
from ...jupyter.utils import get_template
from ...pipeline.display.activity.utils import latest_activity, activity_times_by_group

log = getLogger(__name__)


class Jupyter:

    def __init__(self, config):
        self.__config = config

    def __call__(self, request, s, template):
        log.info(f'Attempting to display template {template}')
        fn, spec = get_template(template)
        args = [request.args[arg] for arg in spec.args]  # order
        log.debug(f'Template args: {args}')
        name = create_notebook(self.__config, fn, args)
        url = f'{self.__config.args[JUPYTER]}/{name}'
        log.debug(f'Redirecting to {url}')
        return redirect(url)

    @staticmethod
    def read_parameters(request, s):
        # odds and sods used to set menus in jupyter URLs
        latest = latest_activity(s)
        times_by_group = activity_times_by_group(s)
        all_activity_times = sorted(sum(times_by_group.values(), []), reverse=True)
        return {'all_activity_times': all_activity_times,
                'activity_times_by_group': times_by_group,
                'latest_activity_group': latest.activity_group.name if latest else None}
