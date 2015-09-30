from __future__ import absolute_import

from email.mime.base import MIMEBase

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail.message import EmailMultiAlternatives

from .connection import Connection


class GoCannonBackend(BaseEmailBackend):
    """
    Django email backend for go-cannon.
    """

    def __init__(self, **kwargs):
        """
        Initialize the connection to go-cannon.
        """
        super(GoCannonBackend, self).__init__(**kwargs)
        self._connection = Connection(
            host=getattr(settings, 'GO_CANNON_HOST', 'localhost'),
            port=getattr(settings, 'GO_CANNON_PORT', 8025),
            tls=getattr(settings, 'GO_CANNON_TLS', False),
            username=getattr(settings, 'GO_CANNON_USERNAME', None),
            password=getattr(settings, 'GO_CANNON_PASSWORD', None),
        )

    def _process_attachments(self, email):
        """
        Convert the attachments in the email to the appropriate format for
        sending with Connection.send().
        """
        for a in email.attachments:
            if isinstance(a, MIMEBase):
                if not a.is_multipart():
                    # TODO: we could avoid decoding base64 content if there
                    # were an easy way to determine if it was already
                    # base64-encoded
                    yield {
                        'filename': a.get_filename(),
                        'content_type': a.get_content_type(),
                        'content': a.get_payload(decode=True),
                    }
            else:
                yield {
                    'filename': a[0],
                    'content_type': a[2],
                    'content': a[1],
                }

    def send_messages(self, emails):
        """
        Attempt to send the specified emails.
        """
        num_sent = 0
        for e in emails:
            html = None
            if isinstance(e, EmailMultiAlternatives):
                for a in e.alternatives:
                    if a[1] == 'text/html':
                        html = a[0]
            r = self._connection.send(
                from_=e.from_email,
                to=e.to,
                subject=e.subject,
                text=e.body,
                html=html,
                cc=e.cc,
                bcc=e.bcc,
                attachments=list(self._process_attachments(e)),
            )
            if 'error' not in r:
                num_sent += 1
        return num_sent
