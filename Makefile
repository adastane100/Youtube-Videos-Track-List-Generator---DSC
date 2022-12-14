SUBDIRS = frontend logs downloading-service recognition-service segmenting-service uniqueness-service

project:
	for dir in $(SUBDIRS); do \
		$(MAKE) build -C $$dir; \
	done