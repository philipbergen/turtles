FROM progrium/busybox
RUN opkg-install git bash openssh-client
COPY repo_setup /
COPY .ssh /root/.ssh
ENTRYPOINT ["/bin/bash", "/repo_setup"]
