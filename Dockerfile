FROM centos:7

RUN curl -sSL http://dl.marmotte.net/rpms/redhat/el6/x86_64/storcli-1.16.06-2/storcli-1.16.06-2.x86_64.rpm > /tmp/storcli.rpm \
&& rpm -ivh /tmp/storcli.rpm \
&& rm /tmp/storcli.rpm

COPY . /

ENTRYPOINT ["/entrypoint.sh"]
