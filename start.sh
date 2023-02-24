setup:
  python38, gcc
 
install:
  python -m venv /opt/venv && . /opt/venv/bin/activate && pip install -r requirements.txt
  install -Dm755 start.sh $out/bin/start
 
start:
  $out/bin/start