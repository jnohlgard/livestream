#!/usr/bin/env python3

import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst
from gi.repository import GLib

GObject.threads_init()
Gst.init(None)


class Sender:
    def __init__(self):
        # Create GStreamer pipeline
        self.pipeline = Gst.Pipeline()

        # Create bus to get events from GStreamer pipeline
        self.bus = self.pipeline.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect('message::error', self.on_error)

        # gst-launch-1.0 -v v4l2src do-timestamp=true \! \
        # video/x-raw, format=\(string\)YUY2, \
        # width=\(int\)640, height=\(int\)480, \
        # framerate=\(fraction\)60/1 \! \
        # videoconvert \! \
        # x264enc speed-preset=ultrafast tune=zerolatency intra-refresh=true \
        # vbv-buf-capacity=0 qp-min=21 pass=qual quantizer=24 byte-stream=true \
        # key-int-max=30 \! \
        # rtph264pay \! \
        # udpsink host=192.168.21.241 port=42146 auto-multicast=false

        # Create GStreamer elements
        # Video source device
        self.src = Gst.ElementFactory.make('v4l2src', None)
        self.src.set_property('do-timestamp', True)
        # conversion pipeline
        #~ self.srccaps = Gst.Caps.from_string("video/x-raw, format=(string)I420, width=(int)640, height=(int)480, framerate=(fraction)60/1")
        self.conversion = Gst.ElementFactory.make('videoconvert', None)
        self.dstcaps = Gst.Caps.from_string("video/x-raw, framerate=(fraction)30/1")

        # Video encoder
        self.encoder = Gst.ElementFactory.make('x264enc', None)
        self.encoder.set_property('speed-preset', 'ultrafast')
        self.encoder.set_property('tune', 'zerolatency')
        self.encoder.set_property('intra-refresh', True)
        self.encoder.set_property('vbv-buf-capacity', 0)
        self.encoder.set_property('qp-min', 21)
        self.encoder.set_property('pass', 'qual')
        self.encoder.set_property('quantizer', 24)
        self.encoder.set_property('byte-stream', True)
        self.encoder.set_property('key-int-max', 30)
        # Network streaming over RTP/UDP
        self.rtp = Gst.ElementFactory.make('rtph264pay', None)
        self.udp = Gst.ElementFactory.make('udpsink', None)
        self.udp.set_property('host', '127.0.0.1')
        self.udp.set_property('port', 42146)
        self.udp.set_property('auto-multicast', False)

        # Add elements to the pipeline
        self.pipeline.add(self.src)
        self.pipeline.add(self.conversion)
        self.pipeline.add(self.encoder)
        self.pipeline.add(self.rtp)
        self.pipeline.add(self.udp)

        self.src.link_filtered(self.conversion, self.srccaps)
        self.conversion.link_filtered(self.encoder, self.dstcaps)
        self.encoder.link(self.rtp)
        self.rtp.link(self.udp)

    def run(self):
        self.pipeline.set_state(Gst.State.PLAYING)
        GLib.MainLoop().run()

    def on_error(self, bus, msg):
        print('on_error():', msg.parse_error())


if __name__ == '__main__':
    sender = Sender()
    sender.run()
