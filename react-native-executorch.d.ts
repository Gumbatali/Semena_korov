declare module 'react-native-executorch' {
  export function useExecuTorchModule(options: {
    modelPath: string;
  }): { module: any };

  export namespace ProcessTensor {
    export function fromImage(uri: string, options: { size: number }): any;
  }
}