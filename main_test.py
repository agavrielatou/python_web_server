from multiprocessing import Process
import aiounittest
import asyncio
import aiohttp
import os
import requests
import time
import sys
import uvicorn

class Testing(aiounittest.AsyncTestCase):

    def setUp(self):
        """ Bring server up. """
        os.environ["CAPACITY"] = "5"
        # 3 seconds in the rate is chosen for the tests
        # in order for the multiple requests to have enough
        # time to be executed in case 1s is not enough
        # in some machines.
        os.environ["MAX_SECONDS"] = "3"

        self.proc = Process(target=uvicorn.run, args=("main:app",), daemon=True)
        self.proc.start()
        time.sleep(1)  # time for the server to start

    def tearDown(self):
        """ Terminate the server. """
        self.proc.terminate()

    def test_post_request_success(self):
        """ Send POST valid request. 200 response status expected """
        data = {
            "product_id": "123",
        }
        response = requests.post('http://localhost:8000/eshop_creation',
            json=data
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual( b'"True"', response.content)

    def test_get_request_failure(self):
        """ Send GET valid request. 405 response status expected """
        response = requests.get('http://localhost:8000/eshop_creation')
        self.assertEqual(405, response.status_code)

    def test_put_request_failure(self):
        """ Send PUT valid request. 405 response status expected """
        data = {
            "product_id": "123",
        }
        response = requests.put('http://localhost:8000/eshop_creation',
            json=data
        )
        self.assertEqual(405, response.status_code)

    def test_delete_request_failure(self):
        """ Send DELETE valid request. 405 response status expected """
        response = requests.delete('http://localhost:8000/eshop_creation')
        self.assertEqual(405, response.status_code)

    def test_post_request_invalid_data(self):
        """ Send POST invalid request with invalid data.
            422 response status expected """
        data = {
            "bla": "123",
        }
        response = requests.post('http://localhost:8000/eshop_creation',
            json=data
        )
        self.assertEqual(422, response.status_code)

    def test_post_request_invalid_endpoint(self):
        """ Send POST invalid request with invalid endpoint.
            404 response status expected
        """
        data = {
            "product_id": "123",
        }
        response = requests.post('http://localhost:8000/invalid_endpoint',
            json=data
        )
        self.assertEqual(404, response.status_code)

    def test_post_request_empty_data(self):
        """ Send POST invalid request with empty data.
            422 response status expected
        """
        data = {}
        response = requests.post('http://localhost:8000/eshop_creation',
            json=data
        )
        self.assertEqual(422, response.status_code)

    def send_multiple_post_requests(self, number_of_requests, endpoint):
        """ Send multiple valid POST requests based
            on the given number_of_requests. """
        data = {
            "product_id": "123",
        }
        responses = []
        url = 'http://localhost:8000/' + endpoint
        for i in range(number_of_requests):
            response = requests.post(url, json=data)
            responses.append(response)
            # don't sleep between the requests

        return responses

    def test_6_post_requests_to_eshop_creation(self):
        """ Send 6 POST requests to eshop_creation endpoint
            with max rate 5 per 3 seconds.
            200 response status expected for them. """
        responses = self.send_multiple_post_requests(6, "eshop_creation")
        for response in responses:
            self.assertEqual(200, response.status_code)
            self.assertEqual( b'"True"', response.content)

    def test_6_post_requests_to_product_then_3_more(self):
        """ Send 6 POST requests to /product with max rate
            5 per 3 seconds. 5 of them will return 200. 1 of them
            will return 429.
            Then sleep for 3 seconds and send 3 more. The final 3
            responses should return 200. """
        responses = self.send_multiple_post_requests(6, "product")
        i = 0
        for response in responses:
            if i < 5:
                self.assertEqual(200, response.status_code)
            else:
                self.assertEqual(429, response.status_code)
            i += 1

        time.sleep(3)

        responses = self.send_multiple_post_requests(3, "product")
        for response in responses:
            self.assertEqual(200, response.status_code)

