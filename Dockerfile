FROM naytseyd/sedenbot:j1xlte

# Working Directory
WORKDIR /DerUntergang/

# Clone Repo
RUN git clone -b alphonse https://github.com/TeamAlphonse/Alphonse.git /DerUntergang/

# Run bot
CMD ["python3", "alphonse.py"]