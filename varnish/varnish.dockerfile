# Use the official varnish image as the base
FROM varnish:latest

# set the user to root, and install build dependencies
USER root
RUN set -e; \
    apt-get update; \
    apt-get -y install libmhash-dev $VMOD_DEPS /pkgs/*.deb; \
    \
    # install one, possibly multiple vmods
    install-vmod https://github.com/varnish/libvmod-digest/releases/download/libvmod-digest-1.0.3/libvmod-digest-1.0.3.tar.gz; \
    \
    # clean up and set the user back to varnish
    apt-get -y purge --auto-remove $VMOD_DEPS varnish-dev; \
    rm -rf /var/lib/apt/lists/*

COPY default.vcl /etc/varnish/

USER varnish
EXPOSE 80 8443
CMD []