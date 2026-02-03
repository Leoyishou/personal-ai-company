#import <Foundation/Foundation.h>
#import <React/RCTBridgeModule.h>

// 注意：将下面的头文件名改为 <你的 Product Module Name>-Swift.h
// 若你的 Xcode Target 名称为 DejavuHybrid，则如下行正确；否则请替换。
#import "DejavuHybrid-Swift.h"

@interface AudioController : NSObject <RCTBridgeModule>
@end

@implementation AudioController
RCT_EXPORT_MODULE();

RCT_EXPORT_METHOD(toggle)
{
  [[AudioCenter shared] toggle];
}

RCT_EXPORT_METHOD(play)
{
  [[AudioCenter shared] play];
}

RCT_EXPORT_METHOD(pause)
{
  [[AudioCenter shared] pause];
}

RCT_REMAP_METHOD(isPlaying,
                 isPlayingWithResolver:(RCTPromiseResolveBlock)resolve
                 rejecter:(RCTPromiseRejectBlock)reject)
{
  BOOL playing = [[AudioCenter shared] isPlayingValue];
  resolve(@(playing));
}

@end

