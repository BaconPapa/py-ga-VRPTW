# -*- coding: utf-8 -*-
# sample_R101.py

import random
from gavrptw.core import gaVRPTW


def main():
    random.seed(64)

    instName = 'R101'

    unitCost = 1.0
    initCost = 0.0
    waitCost = 0.0
    delayCost = 0.0

    indSize = 100
    popSize = 500
    cxPb = 0.85
    mutPb = 0.01
    NGen = 1000

    exportCSV = True

    gaVRPTW(
        instName=instName,
        unitCost=unitCost,
        initCost=initCost,
        waitCost=waitCost,
        delayCost=delayCost,
        indSize=indSize,
        popSize=popSize,
        cxPb=cxPb,
        mutPb=mutPb,
        NGen=NGen,
        exportCSV=exportCSV
    )


if __name__ == '__main__':
    main()