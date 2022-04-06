STUNNEL := stunnel
STUNNEL_VERS := 5.63
STUNNEL_DIR := $(STUNNEL)-$(STUNNEL_VERS)

STUNNEL_UNPACK := $(BUILD_HELPER_DIR)/$(STUNNEL_DIR)-unpack
STUNNEL_BUILD := $(BUILD_HELPER_DIR)/$(STUNNEL_DIR)-build
STUNNEL_INSTALL := $(BUILD_HELPER_DIR)/$(STUNNEL_DIR)-install
STUNNEL_SKEL := $(BUILD_HELPER_DIR)/$(STUNNEL_DIR)-skel

#STUNNEL_INSTALL_DIR := $(INTERMEDIATE_INSTALL_BASE)/$(STUNNEL_DIR)
STUNNEL_BUILD_DIR := $(PACKAGE_BUILD_DIR)/$(STUNNEL_DIR)
#STUNNEL_WORK_DIR := $(PACKAGE_WORK_DIR)/$(STUNNEL_DIR)

$(STUNNEL_BUILD): $(STUNNEL_UNPACK)
	cd $(STUNNEL_BUILD_DIR) && \
	    ./configure \
		--prefix=$(OMD_ROOT)
	$(MAKE) -C $(STUNNEL_BUILD_DIR) -j4
	$(TOUCH) $@

$(STUNNEL_INSTALL): $(STUNNEL_BUILD)
	$(MAKE) -C $(STUNNEL_BUILD_DIR) DESTDIR=$(DESTDIR) install
	rm -f $(DESTDIR)$(OMD_ROOT)/etc/stunnel/stunnel.conf-sample
	rmdir $(DESTDIR)$(OMD_ROOT)/etc/stunnel
	rmdir $(DESTDIR)$(OMD_ROOT)/etc || true
	rmdir $(DESTDIR)$(OMD_ROOT)/var/lib/stunnel
	rmdir $(DESTDIR)$(OMD_ROOT)/var/lib || true
	rmdir $(DESTDIR)$(OMD_ROOT)/var || true
	rm -f $(DESTDIR)/usr/share/bash-completion/completions/stunnel.bash
	rmdir -p --ignore-fail-on-non-empty $(DESTDIR)/usr/share/bash-completion/completions
	$(TOUCH) $@
