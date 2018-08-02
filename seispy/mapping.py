# coding=utf-8
import numpy as np
import mpl_toolkits.basemap as bm
import pkg_resources

DEFAULT_KWARGS = {
        "latmin": 32.5,
        "lonmin": -117.5,
        "latmax": 34.5,
        "lonmax": -115.5,
        "bgstyle": "basic",
        "fill_color": "aqua",
        "continent_color": "coral",
        "lake_color": "aqua",
        "projection": "cyl",
        "meridian_stride": 1,
        "meridian_labels": [False, False, False, True],
        "parallel_stride": 1,
        "parallel_labels": [True, False, False, False],
        "fault_color": "k",
        "fault_linewidth": 1,
        }

class Basemap(bm.Basemap):
    def __init__(self, **kwargs):
        import warnings
        warnings.filterwarnings("ignore")

        for key in DEFAULT_KWARGS:
            if key not in kwargs:
                kwargs[key] = DEFAULT_KWARGS[key]
        self.kwargs = kwargs
        del(kwargs)

        kwargs = {"llcrnrlat": self.kwargs["latmin"],
                  "llcrnrlon": self.kwargs["lonmin"],
                  "urcrnrlat": self.kwargs["latmax"],
                  "urcrnrlon": self.kwargs["lonmax"]}

        if self.kwargs["bgstyle"] == "relief":
            kwargs["projection"] = self.kwargs["projection"]

        super(self.__class__, self).__init__(**kwargs)

        if self.kwargs["bgstyle"] == "basic":
            self._basic_background()
        elif self.kwargs["bgstyle"] == "relief":
            self._relief_background()

        if self.kwargs["meridian_stride"] is not None:
            self.drawmeridians(np.arange(-180,
                                         180,
                                         self.kwargs["meridian_stride"]),
                               labels=self.kwargs["meridian_labels"])
        if self.kwargs["parallel_stride"] is not None:
            self.drawparallels(np.arange(-90,
                                         90,
                                         self.kwargs["parallel_stride"]),
                               labels=self.kwargs["parallel_labels"])

    def _basic_background(self):
        self.drawmapboundary(fill_color=self.kwargs["fill_color"],
                             zorder=0)
        self.fillcontinents(color=self.kwargs["continent_color"],
                            lake_color=self.kwargs["lake_color"],
                            zorder=1)
        self.drawcoastlines(zorder=1)

    def _relief_background(self):
        self.arcgisimage(service="World_Shaded_Relief",
                         xpixels=3000,
                         verbose=True)


    def node_statistic(self, x, y, z, r,
                       func=np.mean,
                       dx=0,
                       dy=0,
                       **kwargs):
        x = np.asarray(x)
        y = np.asarray(y)
        z = np.asarray(z)
        if dx <= 0:
            dx = (x.max() - x.min()) / 9
        if dy <= 0:
            dy = (y.max() - y.min()) / 9
        xnodes = np.arange(x.min(), x.max()+3*dx/2, dx)
        ynodes = np.arange(y.min(), y.max()+3*dy/2, dy)
        XX, YY = np.meshgrid(xnodes, ynodes, indexing="ij")
        ZZ = np.zeros(XX.shape)
        for ix, iy in [(ix, iy) for ix in range(XX.shape[0])
                                for iy in range(XX.shape[1])]:
            dist = np.sqrt(np.square(x-XX[ix, iy]) + np.square(y-YY[ix, iy]))
            idx = dist < r
            ZZ[ix, iy] = func(z[idx]) if np.any(idx) else np.inf
        XX = XX - dx/2
        YY = YY - dy/2
        qmesh = self.pcolormesh(XX, YY, ZZ,
                                zorder=3,
                                **kwargs)
        return(qmesh)

    def add_faults(self, **kwargs):
        if "color" not in kwargs:
            kwargs["color"] = self.kwargs["fault_color"]
        if "linewidth" not in kwargs:
            kwargs["linewidth"] = self.kwargs["fault_linewidth"]
        faults = CaliforniaFaults()
        return(
            [self.plot(segment[:,0], segment[:,1], **kwargs)
                for segment in faults.subset(self.latmin, self.latmax,
                                            self.lonmin, self.lonmax)]
        )

class FaultCollection(object):
    def __init__(self, infile):
        inf = open(infile)
        #: Doc comment for instance attribute data
        self.data = np.array([
                                np.array([[float(coord) for coord in pair.split()]
                                 for pair in chunk.strip().split("\n")
                                ])
                             for chunk in inf.read().split(">")
                             ])
        inf.close()

    def subset(self, latmin, latmax, lonmin, lonmax):
        cond1 = lambda coords: latmin <= coords[1] <= latmax and\
                               lonmin <= coords[0] <= lonmax
        cond2 = lambda segment: np.any([cond1(coords) for coords in segment])
        return(np.asarray(list(filter(cond2, self.data))))

class CaliforniaFaults(FaultCollection):
    def __init__(self):
        fname = pkg_resources.resource_filename("seispy",
                                                "data/ca_scitex.flt")
        super(self.__class__, self).__init__(fname)
