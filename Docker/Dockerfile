FROM ubuntu:jammy

RUN apt-get update && \
    apt-get install -y \
    curl \
    wget \
    unzip \ 
    zip \
    openjdk-17-jdk \
    python3 \
    python3-pip \
    qtbase5-dev \
    libxcb-cursor0 \
    libxkbcommon-x11-0 \
    libegl1 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV GROOVY_HOME=/opt/groovy-4.0.22
ENV PATH=$JAVA_HOME/bin:$GROOVY_HOME/bin:$PATH

RUN cd /usr/bin && \
    ln -sf /usr/bin/python3 /usr/local/bin/python && \
    pip3 --no-cache-dir install --upgrade pip 

COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt
RUN python3 -m spacy download en_core_web_md

RUN curl -L "https://groovy.jfrog.io/ui/api/v1/download?repoKey=dist-release-local&path=groovy-zips%252Fapache-groovy-sdk-4.0.22.zip&isNativeBrowsing=true" -o groovy.zip && \
unzip -q groovy.zip -d /opt 

WORKDIR /PrivacyGuard

CMD ["bash"]
