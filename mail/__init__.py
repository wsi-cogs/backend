import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from bs4 import BeautifulSoup


def send_email(*, host, port, to, from_, subject, contents):
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = from_
    message["To"] = to

    html = contents
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text()

    message.attach(MIMEText(text, 'plain'))
    message.attach(MIMEText(html, 'html'))

    s = smtplib.SMTP(host, port)
    s.set_debuglevel(1000)
    s.sendmail(from_, to, message.as_string())
    s.quit()


if __name__ == "__main__":
    import os
    from config import load_config
    config = load_config(os.path.join("config", "config.yaml"))["email"]
    config["from_"] = config["from"]
    del config["from"]
    send_email(to="sb48@sanger.ac.uk", subject="test", contents="<h1>test</h1>", **config)
