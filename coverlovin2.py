# allows for run-py invocation
#
#    pip-run --use-pep517 --quiet git+https://github.com/jtmoon79/coverlovin2@feature/runpy-invoke -- -m coverlovin2 --help
#

from coverlovin2 import app


if __name__ == "__main__":
    app.main()
