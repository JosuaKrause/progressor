help:
	@echo "The following make targets are available:"
	@echo "publish	publish on pypi"
	@echo "clean	clean dist folder"


clean:
	rm -rf dist/*

VERSION=`echo "import progressor;print(progressor.__version__)" | python3 2>/dev/null`

publish:
	@git diff --exit-code 2>&1 >/dev/null && git diff --cached --exit-code 2>&1 >/dev/null || (echo "working copy is not clean" && exit 1)
	@test -z `git ls-files --other --exclude-standard --directory` || (echo "there are untracked files" && exit 1)
	@test `git rev-parse --abbrev-ref HEAD` = "master" || (echo "not on master" && exit 1)
	python3 setup.py sdist bdist_wheel
	twine upload dist/progressor-$(VERSION)-py2.py3-none-any.whl dist/progressor-$(VERSION).tar.gz
	git tag "v$(VERSION)"
	git push origin "v$(VERSION)"
	@echo "successfully deployed $(VERSION)"
