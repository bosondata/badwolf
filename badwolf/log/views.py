# -*- coding: utf-8 -*-
import os
import logging

import deansi
from flask import Blueprint, current_app, send_from_directory, request, abort, Response
from docker import DockerClient


logger = logging.getLogger(__name__)
blueprint = Blueprint('log', __name__)

FOLLOW_LOG_JS = '''<script type="text/javascript">
var observeDOM = (function(){
  var MutationObserver = window.MutationObserver || window.WebKitMutationObserver,
    eventListenerSupported = window.addEventListener;

  return function(obj, callback){
    if( MutationObserver ){
      // define a new observer
      var obs = new MutationObserver(function(mutations, observer){
        if( mutations[0].addedNodes.length || mutations[0].removedNodes.length )
            callback();
      });
      // have the observer observe foo for changes in children
      obs.observe( obj, { childList:true, subtree:true });
    }
    else if( eventListenerSupported ){
      obj.addEventListener('DOMNodeInserted', callback, false);
      obj.addEventListener('DOMNodeRemoved', callback, false);
    }
  };
})();

window.onload = function() {
  window.autoFollow = true;
  window.onscroll = function() {
    if (window.innerHeight + window.pageYOffset >= document.body.offsetHeight - 10) {
      window.autoFollow = true;
    } else {
      window.autoFollow = false;
    }
  };

  observeDOM(document.body, function() {
    if (window.autoFollow) {
      window.scrollTo(window.pageXOffset, document.body.scrollHeight);
    }
  });
}
</script>'''


@blueprint.route('/build/<sha>', methods=['GET'])
def build_log(sha):
    task_id = request.args.get('task_id')
    log_dir = os.path.join(current_app.config['BADWOLF_LOG_DIR'], sha)
    # old log path
    if os.path.exists(os.path.join(log_dir, 'build.html')):
        return send_from_directory(log_dir, 'build.html')

    if not task_id:
        abort(404)

    # new log path
    log_dir = os.path.join(log_dir, task_id)
    if os.path.exists(os.path.join(log_dir, 'build.html')):
        return send_from_directory(log_dir, 'build.html')

    # Try realtime logs
    docker = DockerClient(
        base_url=current_app.config['DOCKER_HOST'],
        timeout=current_app.config['DOCKER_API_TIMEOUT'],
        version='auto',
    )
    containers = docker.containers.list(filters=dict(
        status='running',
        label='task_id={}'.format(task_id),
    ))
    if not containers:
        abort(404)

    # TODO: ensure only 1 container matched task_id
    container = containers[0]

    def _streaming_gen():
        yield '<style>{}</style>'.format(deansi.styleSheet())
        yield FOLLOW_LOG_JS
        yield '<div class="ansi_terminal">'
        buffer = []
        for log in container.logs(stdout=True, stderr=True, stream=True, follow=True):
            char = str(log)
            buffer.append(char)
            if char == '\n':
                yield deansi.deansi(''.join(buffer))
                buffer = []
        if buffer:
            yield deansi.deansi(''.join(buffer))
        yield '</div>'

    return Response(_streaming_gen(), mimetype='text/html;charset=utf-8')


@blueprint.route('/lint/<sha>', methods=['GET'])
def lint_log(sha):
    log_dir = os.path.join(current_app.config['BADWOLF_LOG_DIR'], sha)
    return send_from_directory(log_dir, 'lint.html')
