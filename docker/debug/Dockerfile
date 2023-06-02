FROM --platform=linux/amd64 ubuntu:bionic
WORKDIR /root

RUN sed -i '/path-exclude=\/usr\/share\/man\/*/c\#path-exclude=\/usr\/share\/man\/*' /etc/dpkg/dpkg.cfg.d/excludes

RUN apt-get update -qq && \
    apt-get install -y apt-transport-https \
                       ca-certificates \
                       software-properties-common \
                       man \
                       wget \
                       elasticsearch-curator \
                       manpages-posix \
                       man-db \
                       vim \
                       screen \
                       curl \
                       htop \
                       dstat \
                       jq \
                       dnsutils \
                       tcpdump \
                       traceroute \
                       iputils-ping \
                       net-tools \
                       netcat \
                       iproute2 \
                       simpleproxy \
                       mongodb-clients \
                       strace

RUN curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add - && \
    add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" && \
    apt-get update -qq && \
    apt-get install -y docker-ce

WORKDIR /tmp
RUN wget -q https://dl.min.io/client/mc/release/linux-amd64/mc && \
    chmod +x mc && \
    cp /tmp/mc /usr/bin && \
    rm -rf /tmp/mc

CMD tail -f /dev/null
