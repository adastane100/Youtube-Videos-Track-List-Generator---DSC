SUBDIRS = frontend downloading-service recognition-service segmenting-service 

project:
	for dir in $(SUBDIRS); do \
		$(MAKE) build -C $$dir; \
	done