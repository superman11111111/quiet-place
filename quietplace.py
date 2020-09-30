import requests
from datetime import datetime
import responses
import googlemaps
import unittest
import codecs

from urllib.parse import urlparse, parse_qsl


class TestCase(unittest.TestCase):
  def assertURLEqual(self, first, second, msg=None):
    """Check that two arguments are equivalent URLs. Ignores the order of
      query arguments.
    """
    first_parsed = urlparse(first)
    second_parsed = urlparse(second)
    self.assertEqual(first_parsed[:3], second_parsed[:3], msg)

    first_qsl = sorted(parse_qsl(first_parsed.query))
    second_qsl = sorted(parse_qsl(second_parsed.query))
    self.assertEqual(first_qsl, second_qsl, msg)

  def u(self, string):
    """Create a unicode string, compatible across all versions of Python."""
    # NOTE(cbro): Python 3-3.2 does not have the u'' syntax.
    return codecs.unicode_escape_decode(string)[0]


class RoadsTest(TestCase):
  def __init__(self):
    self.key = "AIzaSyAO5UbTnvql9m4f4muxzld8PijEHNZPFj4"
    self.client = googlemaps.Client(self.key)
    super().__init__()

  @responses.activate
  def test_snap(self):
    responses.add(
        responses.GET,
        "https://roads.googleapis.com/v1/snapToRoads",
        body='{"snappedPoints":["foo"]}',
        status=200,
        content_type="application/json",
        )

    results = self.client.snap_to_roads((40.714728, -73.998672))
    self.assertEqual("foo", results[0])
    self.assertEqual(1, len(responses.calls))
    self.assertURLEqual(
      "https://roads.googleapis.com/v1/snapToRoads?"
      "path=40.714728%%2C-73.998672&key=%s" % self.key,
      responses.calls[0].request.url,
      )

  @responses.activate
  def test_nearest_roads(self):
    responses.add(
        responses.GET,
        "https://roads.googleapis.com/v1/nearestRoads",
        body='{"snappedPoints":["foo"]}',
        status=200,
        content_type="application/json",
        )

    results = self.client.nearest_roads((40.714728, -73.998672))
    self.assertEqual("foo", results[0])

    self.assertEqual(1, len(responses.calls))
    print(responses.calls[0].request.url)
    self.assertURLEqual(
      "https://roads.googleapis.com/v1/nearestRoads?"
      "points=40.714728%%2C-73.998672&key=%s" % self.key,
      responses.calls[0].request.url,
      )

  def find_nearest(self):
    return requests.get("https://roads.googleapis.com/v1/nearestRoads?points=40.714728%%2C-73.998672&key=%s" % self.key)

  @responses.activate
  def test_path(self):
    responses.add(
        responses.GET,
        "https://roads.googleapis.com/v1/speedLimits",
        body='{"speedLimits":["foo"]}',
        status=200,
        content_type="application/json",
        )

    results = self.client.snapped_speed_limits([(1, 2), (3, 4)])
    self.assertEqual("foo", results["speedLimits"][0])

    self.assertEqual(1, len(responses.calls))
    self.assertURLEqual(
      "https://roads.googleapis.com/v1/speedLimits?"
      "path=1%%2C2|3%%2C4"
      "&key=%s" % self.key,
      responses.calls[0].request.url,
      )

  @responses.activate
  def test_speedlimits(self):
    responses.add(
        responses.GET,
        "https://roads.googleapis.com/v1/speedLimits",
        body='{"speedLimits":["foo"]}',
        status=200,
        content_type="application/json",
        )

    results = self.client.speed_limits("id1")
    self.assertEqual("foo", results[0])
    self.assertEqual(
        "https://roads.googleapis.com/v1/speedLimits?"
        "placeId=id1&key=%s" % self.key,
        responses.calls[0].request.url,
        )

    @responses.activate
    def test_speedlimits_multiple(self):
      responses.add(
          responses.GET,
          "https://roads.googleapis.com/v1/speedLimits",
          body='{"speedLimits":["foo"]}',
          status=200,
          content_type="application/json",
          )

      results = self.client.speed_limits(["id1", "id2", "id3"])
      self.assertEqual("foo", results[0])
      self.assertEqual(
          "https://roads.googleapis.com/v1/speedLimits?"
          "placeId=id1&placeId=id2&placeId=id3"
          "&key=%s" % self.key,
          responses.calls[0].request.url,
          )

      def test_clientid_not_accepted(self):
        client = googlemaps.Client(client_id="asdf", client_secret="asdf")

        with self.assertRaises(ValueError):
          client.speed_limits("foo")

      @responses.activate
      def test_retry(self):
        class request_callback:
          def __init__(self):
            self.first_req = True
          def __call__(self, req):
            if self.first_req:
              self.first_req = False
              return (500, {}, "Internal Server Error.")
            return (200, {}, '{"speedLimits":[]}')
            responses.add_callback(
                responses.GET,
                "https://roads.googleapis.com/v1/speedLimits",
                content_type="application/json",
                callback=request_callback(),
                )

        self.client.speed_limits([])
        self.assertEqual(2, len(responses.calls))
        self.assertEqual(responses.calls[0].request.url, responses.calls[1].request.url)

if __name__ == "__main__":
  rt = RoadsTest()
  rt.test_nearest_roads()
  s = rt.find_nearest()
  print(s)
  print(rt)
