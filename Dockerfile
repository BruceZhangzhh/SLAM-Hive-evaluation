FROM python:2.7
RUN wget https://github.com/uzh-rpg/rpg_trajectory_evaluation/archive/v0.1.tar.gz
RUN tar xzf v0.1.tar.gz
RUN cd rpg_trajectory_evaluation-0.1/
RUN pip install numpy
RUN pip install matplotlib
RUN pip install colorama
RUN pip install ruamel.yaml
RUN pip install PyYAML
RUN apt update
RUN apt install -y texlive-full
RUN find / -name 'matplotlibrc' -type f -exec sed -i 's/backend\s*:\s*\w*$/backend: Agg/' {} \;

