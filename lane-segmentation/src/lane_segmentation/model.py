"""#2.model: binary U-Net with encoder-decoder skip connections."""

import torch
from torch import nn
from torch.nn import functional as F


class ConvBlock(nn.Module):
    def __init__(self, input_channels, output_channels):
        super().__init__()
        self.layers = nn.Sequential(
            nn.Conv2d(input_channels, output_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(output_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(output_channels, output_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(output_channels),
            nn.ReLU(inplace=True),
        )

    def forward(self, inputs):
        return self.layers(inputs)


class UNet(nn.Module):
    def __init__(self, in_channels=3, out_channels=1, channels=(32, 64, 128, 256, 512)):
        super().__init__()
        if len(channels) != 5:
            raise ValueError("UNet requires exactly five encoder channel widths")
        self.enc1 = ConvBlock(in_channels, channels[0])
        self.enc2 = ConvBlock(channels[0], channels[1])
        self.enc3 = ConvBlock(channels[1], channels[2])
        self.enc4 = ConvBlock(channels[2], channels[3])
        self.bottleneck = ConvBlock(channels[3], channels[4])
        self.pool = nn.MaxPool2d(kernel_size=2, stride=2)
        self.up4 = nn.ConvTranspose2d(channels[4], channels[3], kernel_size=2, stride=2)
        self.dec4 = ConvBlock(channels[3] * 2, channels[3])
        self.up3 = nn.ConvTranspose2d(channels[3], channels[2], kernel_size=2, stride=2)
        self.dec3 = ConvBlock(channels[2] * 2, channels[2])
        self.up2 = nn.ConvTranspose2d(channels[2], channels[1], kernel_size=2, stride=2)
        self.dec2 = ConvBlock(channels[1] * 2, channels[1])
        self.up1 = nn.ConvTranspose2d(channels[1], channels[0], kernel_size=2, stride=2)
        self.dec1 = ConvBlock(channels[0] * 2, channels[0])
        self.output = nn.Conv2d(channels[0], out_channels, kernel_size=1)

    @staticmethod
    def _match_size(inputs, reference):
        if inputs.shape[-2:] != reference.shape[-2:]:
            inputs = F.interpolate(inputs, size=reference.shape[-2:], mode="bilinear", align_corners=False)
        return inputs

    def forward(self, inputs):
        if inputs.ndim != 4 or inputs.shape[1] != 3:
            raise ValueError(f"Expected input shape [batch, 3, height, width], got {tuple(inputs.shape)}")
        if min(inputs.shape[-2:]) < 16:
            raise ValueError("Input height and width must be at least 16")

        enc1 = self.enc1(inputs)
        enc2 = self.enc2(self.pool(enc1))
        enc3 = self.enc3(self.pool(enc2))
        enc4 = self.enc4(self.pool(enc3))
        bottleneck = self.bottleneck(self.pool(enc4))

        dec4 = self.dec4(torch.cat((self._match_size(self.up4(bottleneck), enc4), enc4), dim=1))
        dec3 = self.dec3(torch.cat((self._match_size(self.up3(dec4), enc3), enc3), dim=1))
        dec2 = self.dec2(torch.cat((self._match_size(self.up2(dec3), enc2), enc2), dim=1))
        dec1 = self.dec1(torch.cat((self._match_size(self.up1(dec2), enc1), enc1), dim=1))
        return self.output(dec1)
