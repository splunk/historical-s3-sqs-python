
import queue_s3_data
import time
import sys
import argparse
import inquirer
import boto3
import pprint

class GUIArgs(object):

    def __init__(self):
        self.bucket = ''
        self.queuename = ''
        self.queueurl = ''
        self.region = ''
        self.start_after = False
        self.prefix = False
        self.verbose = False
        self.time = False

        self.s3 = boto3.client('s3')
        self.sqs = boto3.client('sqs')

        response = self.s3.list_buckets()
        self.buckets = [bucket for bucket in response['Buckets']]
        bucket_choices = [bucket['Name'] for bucket in self.buckets]
        response = self.sqs.list_queues()

        self.queue_urls = [queue for queue in response['QueueUrls']]

        self.questions = [
            inquirer.List(name='queueurl', message='Enter the url of the SQS queue you would like to send messages to', choices=self.queue_urls),
            inquirer.List(name='bucketname', message='Enter the bucket to process events from', choices=bucket_choices),
            inquirer.Text(name='startafter', message='Ingest all records after the specified key in S3. This can be any key in your bucket. (press enter to skip)'),
            inquirer.Text(name='prefix', message='Ingest all records that match the specified prefix (press enter for all records)'),
            inquirer.Confirm(name='verbose', message='Display all names of the files being written'),
            inquirer.Confirm(name='time', message='Display how long the execution takes to run')
        ]

        res = inquirer.prompt(self.questions)
        res['queuename'] = res['queueurl'].split('/')[-1]
        res['region'] = self.s3.get_bucket_location(Bucket=res['bucketname'])['LocationConstraint']
        self.attrs = res
        self.time = res['time']

    def ingest(self):
        start = time.time()
        inst = queue_s3_data.QueueS3Data(**self.attrs)
        num_events = inst.process_s3()
        end = time.time()
        print("{} events ingested in {} seconds".format(num_events,end-start))

        
class HandleArgs(object):

    def __init__(self):

        self.queue_name = ''
        self.bucket_name = ''
        self.queue_url = ''
        self.region = ''
        self.start_after = False
        self.prefix = False
        self.verbose = False
        self.time = False

        self.attrs = {}

        self.parser = argparse.ArgumentParser(description='Process aws options')

        self.parser.add_argument('queueurl', help='the url of the SQS queue you would like to send messages to (required)')
        self.parser.add_argument('bucket', help='the bucket to process events from (required)')
        self.parser.add_argument('region', help='the region both the bucket and the queue are in (required)')
        self.parser.add_argument('--startafter', help='ingest all records after the specified key in S3.  This can be any key in your bucket.')
        self.parser.add_argument('--prefix', help='ingest all records that match the specified prefix')
        self.parser.add_argument('--verbose', help='Display all names of the files being written (default: false)', action="store_true")
        self.parser.add_argument('--time', help='Display how long the execution takes to run (default: false)', action="store_true")

        args = self.parser.parse_args()

        try:
            self.attrs['queueurl'] = args.queueurl.split("=")[1]
            self.attrs['bucketname'] = args.bucket.split("=")[1]
            self.attrs['region'] = args.region.split("=")[1]
            self.attrs['queuename'] = self.attrs['queueurl'].split('/')[-1]

            if args.startafter:
                self.attrs['startafter'] = args.startafter

            if args.prefix:
                self.attrs['prefix'] = args.prefix
            
            if args.verbose:
                self.attrs['verbose'] = True

            if args.time:
                self.time = True

        except:
            raise SyntaxError('Invalid syntax. your positional arguments should be in the form queue=myqueuename bucket=mybucketname')

    def ingest(self):
        inst = queue_s3_data.QueueS3Data(**self.attrs)

        if self.time:
            start = self.__timeit()

        num_events = inst.process_s3()

        if self.time:
            end = self.__timeit()
            total_time = end - start
            print("{} events added to {} in {} seconds".format(num_events, self.queue_url, total_time))

        else:
            print("Done")

    def __timeit(self):
        return time.time()


def main():
    inst = GUIArgs()
    inst.ingest()

    # inst = HandleArgs()
    # inst.ingest()

if __name__ == '__main__':
    main()