from services.amazon_service import AmazonService
from services.file_service import FileService

from containers import Container, providers
from dependency_injector.wiring import Provide
from logger import logger


class MultimodalSearchProcessing:
    def __init__(self,
                 amazon_service: AmazonService,
                 file_service: FileService,
                 processing_queue=Provide(Container.config.aws.processing_queue)):

        self.amazon_service = amazon_service
        self.file_service = file_service
        self.processing_queue = processing_queue

    def run(self):
        queue = self.amazon_service.get_queue_by_name(self.processing_queue)

        while True:
            messages = self.amazon_service.receive_message(queue['QueueUrl'])
            for message in messages:
                self.process_message(queue, message)

    def process_message(self, queue, message):
        try:

            logger.debug(f"processing message {message['MessageId']}")
            body = message['Body']

            self.file_service.process(body)

            logger.info(f"{body}")
        except Exception as err:
            logger.error(f"failed to process message {message['MessageId']} {err.__str__()}")
        finally:
            self.amazon_service.delete_message(queue['QueueUrl'], message['ReceiptHandle'])


if __name__ == '__main__':
    container = Container()
    container.init_resources()
    container.wire(modules=[__name__])

    worker = MultimodalSearchProcessing(
        amazon_service=container.amazon_service(),
        file_service=container.file_service()
    )

    logger.info("application started to receive and processing multipart files")
    worker.run()

